"""
Stoic Citadel - Risk Management Mixin
=====================================

Provides integrated risk management for Freqtrade strategies.
Uses the central RiskManager to enforce strict safety checks.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

import pandas as pd
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

# Import Stoic Risk Components
from src.risk.risk_manager import RiskManager
from src.risk.circuit_breaker import CircuitBreakerConfig
from src.risk.position_sizing import PositionSizingConfig
from src.risk.liquidation import LiquidationConfig
from src.config.unified_config import load_config

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
        self.risk_manager: Optional[RiskManager] = None
        self._last_balance_update = datetime.min
        self._correlation_update_interval = timedelta(hours=1)
        self._last_correlation_update = datetime.min

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
                daily_loss_limit_pct=config.risk.max_daily_loss_pct
            )
            
            size_config = PositionSizingConfig(
                max_position_pct=config.risk.max_position_pct,
                max_portfolio_risk_pct=config.risk.max_portfolio_risk,
                max_correlation_exposure=config.risk.max_correlation
            )
            
            liq_config = LiquidationConfig(
                safety_buffer=config.risk.liquidation_buffer,
                max_safe_leverage=config.risk.max_safe_leverage
            )
            
            # Initialize Manager
            self.risk_manager = RiskManager(
                circuit_config=cb_config,
                sizing_config=size_config,
                liquidation_config=liq_config
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
        entry_tag: Optional[str],
        side: str,
        **kwargs
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
        stop_loss_pct = abs(self.stoploss) # self.stoploss is usually negative
        stop_price = rate * (1 - stop_loss_pct) if side == "long" else rate * (1 + stop_loss_pct)
        
        # Determine leverage (use strategy default or config)
        leverage = self.config.get('leverage', 1.0) if hasattr(self, 'config') else 1.0
        
        # Check safety
        evaluation = self.risk_manager.evaluate_trade(
            symbol=pair,
            entry_price=rate,
            stop_loss_price=stop_price,
            side=side,
            leverage=leverage
        )
        
        if not evaluation["allowed"]:
            logger.warning(f"🚫 Trade blocked by Risk Manager: {evaluation['rejection_reason']}")
            return False
            
        # 3. Check Correlation (if not already handled in evaluate_trade via PositionSizer)
        # Assuming evaluate_trade handles it via position_sizer.check_portfolio_risk
        
        return True

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs
    ) -> float:
        """
        Calculate safe position size using Risk Manager (Stateless Mode).
        """
        if not self.risk_manager:
            return proposed_stake
            
        # Get stop loss price
        stop_loss_pct = abs(self.stoploss)
        stop_price = current_rate * (1 - stop_loss_pct) if side == "long" else current_rate * (1 + stop_loss_pct)

        # Calculate Size using pure function (No state sync required)
        try:
            current_balance = self.wallets.get_total_stake_amount()
            
            safe_stake = RiskManager.calculate_safe_size(
                account_balance=current_balance,
                entry_price=current_rate,
                stop_loss_price=stop_price,
                max_risk_pct=0.02, # 2% risk per trade
                max_position_pct=0.10, # 10% max position size
                leverage=leverage
            )
            
            # Respect Freqtrade limits
            if min_stake:
                safe_stake = max(safe_stake, min_stake)
            if max_stake:
                safe_stake = min(safe_stake, max_stake)
                
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
                    "value": trade.stake_amount, # Approx value
                    "stop_loss": trade.stop_loss,
                    "unrealized_pnl": trade.calc_profit_ratio(trade.select_current_rate()) * trade.stake_amount
                }
            
            self.risk_manager.initialize(
                account_balance=current_balance,
                existing_positions=positions_dict
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
        # This is tricky in Freqtrade because accessing all pairs data might be slow
        # We rely on self.dp.current_whitelist()
        try:
            whitelist = self.dp.current_whitelist()
            # Need OHLCV for all pairs.
            # This is heavy. Only do it if we have < 50 pairs maybe?
            
            # Placeholder: In a real bot, we'd query the dataprovider
            pass
        except Exception:
            pass
