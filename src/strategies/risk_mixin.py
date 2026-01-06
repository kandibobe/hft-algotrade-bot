"""
Stoic Citadel - Risk Management Mixin
=====================================

Provides integrated risk management for Freqtrade strategies.
Uses the central RiskManager to enforce strict safety checks.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
from freqtrade.persistence import Trade

from src.config.unified_config import load_config
from src.ml.online_learner import OnlineLearner
from src.risk.circuit_breaker import CircuitBreakerConfig
from src.risk.liquidation import LiquidationConfig
from src.risk.position_sizing import PositionSizingConfig

# Import Stoic Risk Components
from src.risk.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class StoicRiskMixin:
    """
    Mixin class to add professional risk management to any Freqtrade strategy.

    Features:
    - Centralized RiskManager instance
    - Pre-trade validation (Liquidation, Correlation, Circuit Breaker)
    - Dynamic Position Sizing (Volatility/Regime adjusted)
    - Automated Kill Switch
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.risk_manager: RiskManager | None = None
        self.online_learner: OnlineLearner | None = None
        self._last_balance_update = datetime.min
        self._correlation_update_interval = timedelta(hours=1)
        self._last_correlation_update = datetime.min
        self._last_learning_update = datetime.min
        self._processed_trade_ids = set()

    def bot_loop_start(self, **kwargs) -> None:
        """
        Called at the start of each bot iteration.
        Used for periodic maintenance tasks like Online Learning.
        """
        # Call parent if exists (useful if multiple mixins)
        if hasattr(super(), "bot_loop_start"):
            super().bot_loop_start(**kwargs)

        # Initialize Online Learner if needed (lazy init)
        if not self.online_learner:
            try:
                # In a real setup, we might have multiple models per pair
                # For now, we try to load a default production model
                base_model_path = "user_data/models/production_model.pkl"
                # Check if model exists before initializing
                # self.online_learner = OnlineLearner(base_model_path)
                pass
            except Exception as e:
                logger.warning(f"Failed to initialize OnlineLearner: {e}")

        # Periodic Learning (e.g. every 1 hour)
        if datetime.now() - self._last_learning_update > timedelta(hours=1):
            self._learn_from_closed_trades()
            self._last_learning_update = datetime.now()

    def _learn_from_closed_trades(self):
        """
        Fetch recently closed trades and update Online Learner.
        """
        try:
            # Get closed trades from DB
            trades = Trade.get_trades([Trade.is_open.is_(False)]).all()

            for trade in trades:
                if trade.id in self._processed_trade_ids:
                    continue

                # Placeholder for actual online learning update
                # We need features at entry time to update the model
                # logger.info(f"Processing trade {trade.id} for online learning: PnL={trade.close_profit}")

                self._processed_trade_ids.add(trade.id)

        except Exception as e:
            logger.warning(f"Online learning update failed: {e}")

    def bot_start(self, **kwargs) -> None:
        """
        Initialize Risk Manager on bot startup.
        """
        try:
            # Load unified config
            # Note: We assume config file location or load default
            # In production, this should pass the actual config path
            config = load_config()

            # Create configs
            cb_config = CircuitBreakerConfig(
                max_drawdown_pct=config.risk.max_drawdown_pct,
                daily_loss_limit_pct=config.risk.max_daily_loss_pct,
            )

            size_config = PositionSizingConfig(
                max_position_pct=config.risk.max_position_pct,
                max_portfolio_risk_pct=config.risk.max_portfolio_risk,
                max_correlation_exposure=config.risk.max_correlation,
            )

            liq_config = LiquidationConfig(
                safety_buffer=config.risk.liquidation_buffer,
                max_safe_leverage=config.risk.max_safe_leverage,
            )

            # Initialize Manager
            self.risk_manager = RiskManager(
                circuit_config=cb_config, sizing_config=size_config, liquidation_config=liq_config
            )

            # Validate Config for Safety
            if config:
                issues = config.validate_for_live_trading()
                if issues:
                    warning_msg = "\n".join([f"⚠️ {issue}" for issue in issues])
                    logger.warning(f"Configuration Safety Warnings:\n{warning_msg}")
                    # In live mode (not dry_run), we might want to be stricter
                    if not config.dry_run and any("High leverage" in i for i in issues):
                        logger.error(
                            "CRITICAL: High leverage in live trading! Proceed with caution."
                        )

            logger.info("✅ Stoic Risk Mixin Initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Risk Manager: {e}")
            # Freqtrade swallows exceptions in bot_start often, so we log heavily

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> bool:
        """
        Mandatory pre-trade check hook.
        """
        if not self.risk_manager:
            logger.warning("Risk Manager not initialized - allowing trade but unsafe!")
            return True

        # Update Risk Manager state
        self._sync_risk_state()

        # 1. Check Circuit Breaker
        if not self.risk_manager.circuit_breaker.can_trade():
            logger.warning(f"🚫 Trade blocked by Circuit Breaker: {pair}")
            return False

        # 2. Check Liquidation Safety
        # We need a stop loss to check safety. Freqtrade doesn't pass SL here directly
        # unless we calculated it before. We'll use the strategy's default stoploss.
        stop_loss_pct = abs(self.stoploss)  # self.stoploss is usually negative
        stop_price = rate * (1 - stop_loss_pct) if side == "long" else rate * (1 + stop_loss_pct)

        # Determine leverage (use strategy default or config)
        leverage = self.config.get("leverage", 1.0) if hasattr(self, "config") else 1.0

        # Check safety
        evaluation = self.risk_manager.evaluate_trade(
            symbol=pair, entry_price=rate, stop_loss_price=stop_price, side=side, leverage=leverage
        )

        # 3. Extra Safety Check: Price Deviation
        # Prevent entry if price has deviated too much from the signal price (if available)
        # Or if price is extremely far from EMA (flash crash protection)
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if not dataframe.empty:
            last_candle = dataframe.iloc[-1]
            ema_200 = last_candle.get("ema_200")
            if ema_200 and rate < ema_200 * 0.7:  # 30% deviation from 200 EMA
                logger.warning(f"🚫 Trade blocked: Extreme price deviation from EMA200 for {pair}")
                return False

        if not evaluation["allowed"]:
            logger.warning(f"🚫 Trade blocked by Risk Manager: {evaluation['rejection_reason']}")
            return False

        # 3. Check Correlation (if not already handled in evaluate_trade via PositionSizer)
        # Assuming evaluate_trade handles it via position_sizer.check_portfolio_risk

        return True

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | None:
        """
        Check for emergency exit conditions.
        """
        if self.risk_manager and self.risk_manager.emergency_exit:
            return "emergency_exit"

        return None

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """
        Calculate position size using Inverse Volatility Sizing (Capital Guardian).

        Formula: Size = (Equity * Target_Risk) / ATR_Pct
        """
        if not self.risk_manager:
            return proposed_stake

        try:
            # 1. Get Equity (Total - including locked in orders if possible)
            # Freqtrade's get_total_stake_amount usually includes open orders
            current_balance = self.wallets.get_total_stake_amount()

            # 2. Get Volatility (ATR)
            # We need the dataframe to calculate ATR Pct
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            last_candle = dataframe.iloc[-1].squeeze()

            # Default to 2% if ATR missing (safety fallback)
            atr_pct = last_candle.get("atr_percent", 0.02)
            if pd.isna(atr_pct) or atr_pct == 0:
                atr_pct = 0.02

            # 3. Inverse Volatility Sizing
            # Target Risk: 1% of Equity per trade
            TARGET_RISK_PER_TRADE = 0.01

            # Size = (Equity * 0.01) / ATR_Pct
            # Example: Eq=1000, Risk=10, ATR=2% (0.02) -> Size = 500
            # Example: Eq=1000, Risk=10, ATR=5% (0.05) -> Size = 200
            raw_size = (current_balance * TARGET_RISK_PER_TRADE) / atr_pct

            # 4. Drawdown Suppression (The Brake Pedal)
            # If we are in drawdown, reduce size
            # We estimate drawdown from RiskManager metrics if available
            metrics = self.risk_manager.get_metrics()
            current_dd = float(metrics.current_drawdown_pct)  # e.g. 0.05 for 5%

            # Suppression Logic: Reduce size by 50% if DD > 5%
            dd_factor = 1.0
            if current_dd > 0.05:
                dd_factor = 0.5
                logger.info(
                    f"Drawdown Suppression Active (DD={current_dd:.1%}): Sizing reduced by 50%"
                )

            safe_stake = raw_size * dd_factor

            # 5. Hard Caps
            # Never risk more than 20% of equity on one trade (Safety Cap)
            max_position_cap = current_balance * 0.20
            safe_stake = min(safe_stake, max_position_cap)

            # Respect Freqtrade limits
            if min_stake:
                safe_stake = max(safe_stake, min_stake)
            if max_stake:
                safe_stake = min(safe_stake, max_stake)

            logger.info(
                f"Sizing: Bal={current_balance:.0f} ATR={atr_pct:.1%} DD={current_dd:.1%} -> Stake={safe_stake:.2f}"
            )

            return safe_stake

        except Exception as e:
            logger.error(f"Error in custom_stake_amount: {e}")
            return proposed_stake

    def _sync_risk_state(self):
        """
        Synchronize Freqtrade state (wallets, positions) to RiskManager.
        """
        if not self.risk_manager:
            return

        # Update Balance
        try:
            current_balance = self.wallets.get_total_stake_amount()

            # Map Freqtrade trades to RiskManager positions format
            # self.get_trades() returns Trade objects
            open_trades = Trade.get_trades([Trade.is_open.is_(True)]).all()

            positions_dict = {}
            for trade in open_trades:
                positions_dict[trade.pair] = {
                    "entry_price": trade.open_rate,
                    "size": trade.amount,
                    "value": trade.stake_amount,  # Approx value
                    "stop_loss": trade.stop_loss,
                    "unrealized_pnl": trade.calc_profit_ratio(trade.select_current_rate())
                    * trade.stake_amount,
                }

            self.risk_manager.initialize(
                account_balance=current_balance, existing_positions=positions_dict
            )

            # Update Correlation Matrix periodically
            if datetime.now() - self._last_correlation_update > self._correlation_update_interval:
                self._update_correlation_matrix()
                self._last_correlation_update = datetime.now()

        except Exception as e:
            logger.warning(f"Failed to sync risk state: {e}")

    def _update_correlation_matrix(self):
        """
        Fetch data and update correlation matrix.
        """
        try:
            # Check if DataProvider is available
            if not hasattr(self, "dp") or not self.dp:
                return

            whitelist = self.dp.current_whitelist()
            if not whitelist:
                return

            # Fetch data for all pairs (last 24h * 60m/5m candles approx)
            # Use '1h' timeframe for correlation to reduce noise and data size
            # We assume 1h data is available. If not, fallback to strategy timeframe.
            corr_timeframe = "1h"
            candle_count = 100  # 100 hours history

            close_prices = {}

            for pair in whitelist:
                try:
                    # Get pair data
                    # Note: get_pair_dataframe might return None or empty DF
                    df = self.dp.get_pair_dataframe(pair, corr_timeframe)

                    if df is None or df.empty:
                        # Fallback to strategy timeframe
                        df = self.dp.get_pair_dataframe(pair, self.timeframe)

                    if df is not None and not df.empty:
                        # Take last N rows to ensure recent correlation
                        # Ensure 'date' is index for alignment
                        if "date" in df.columns:
                            df = df.set_index("date")

                        df = df.iloc[-candle_count:]
                        close_prices[pair] = df["close"]
                except Exception as e:
                    logger.warning(f"Could not fetch data for {pair}: {e}")

            if not close_prices:
                return

            # Create DataFrame (aligns on datetime index)
            prices_df = pd.DataFrame(close_prices)

            # Calculate returns
            returns_df = prices_df.pct_change().dropna()

            if returns_df.empty:
                return

            # Update analyzer
            if self.risk_manager and self.risk_manager.correlation_analyzer:
                self.risk_manager.correlation_analyzer.calculate_portfolio_correlation(returns_df)
                logger.info(f"Updated correlation matrix for {len(returns_df.columns)} pairs")

        except Exception as e:
            logger.error(f"Error updating correlation matrix: {e}")
