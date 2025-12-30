"""
Stoic Citadel - Ensemble Strategy V5 (Regime-Adaptive)
======================================================

Features:
1. Regime-Adaptive Logic: Switches behavior based on Hurst Exponent and Volatility Rank.
2. Statistical Robustness: Uses Percentile Ranks instead of fixed thresholds.
3. Random Walk Filter: Blocks trades when market lacks structure.
4. Volatility Scaling: Position sizing inversely proportional to volatility rank.

Philosophy: "Don't fight the regime. Surf the waves, fade the chop, sit out the noise."

Author: Stoic Citadel Team
Version: 5.2.0 (Regime Refactor)
"""

import sys
from pathlib import Path
# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from functools import reduce

import pandas as pd
import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, CategoricalParameter
from freqtrade.persistence import Trade

# Imports
try:
    from src.utils.regime_detection import calculate_regime, get_market_regime
    # We still use V4's ML integration helper functions if we want to keep ML
    from src.ml.model_loader import get_production_model
    # Import Risk Mixin
    from src.strategies.risk_mixin import StoicRiskMixin
    # Import Core Logic
    from src.strategies.core_logic import StoicLogic
    # Import Hybrid Connector
    from src.strategies.hybrid_connector import HybridConnectorMixin
    USE_CUSTOM_MODULES = True
except ImportError as e:
    USE_CUSTOM_MODULES = False
    import talib.abstract as ta
    logging.getLogger(__name__).warning(f"Custom modules not available: {e}")
    # Dummy mixin if import fails
    class StoicRiskMixin: pass
    class StoicLogic: pass
    class HybridConnectorMixin: pass

logger = logging.getLogger(__name__)

class StoicEnsembleStrategyV5(HybridConnectorMixin, StoicRiskMixin, IStrategy):
    INTERFACE_VERSION = 3

    # Hyperparameters
    # Buy Params
    buy_rsi = IntParameter(20, 40, default=30, space="buy")
    
    # ML
    ml_weight = DecimalParameter(0.3, 0.7, default=0.5, space="buy")
    entry_prob_threshold = DecimalParameter(0.55, 0.8, default=0.6, space="buy")

    # Sell Params
    sell_rsi = IntParameter(65, 85, default=75, space="sell")
    
    # Risk
    stoploss_atr_mult = DecimalParameter(1.5, 4.0, default=2.5, space="sell")
    
    # Timeframe
    timeframe = '5m'
    startup_candle_count = 500  # Needed for robust Volatility Rank & Hurst

    # ROI (Dynamic via Hyperopt)
    minimal_roi = {
        "0": 0.20,
        "30": 0.10,
        "60": 0.05,
        "120": 0.02
    }
    
    stoploss = -0.10  # Fallback, overridden by custom_stoploss
    trailing_stop = False # We use custom trailing
    
    use_exit_signal = True
    process_only_new_candles = True
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Calculate indicators."""
        try:
            if USE_CUSTOM_MODULES:
                # 1. Standard Indicators (ATR, RSI, BB, etc.)
                dataframe = StoicLogic.populate_indicators(dataframe)
                
                # 2. Regime Metrics (Z-Score, Hurst, Enum)
                # Calculates over entire history
                regime_df = calculate_regime(
                    dataframe['high'], dataframe['low'], dataframe['close'], dataframe['volume']
                )
                
                # Merge Regime Data
                dataframe['regime'] = regime_df['regime']
                dataframe['vol_zscore'] = regime_df['vol_zscore']
                dataframe['hurst'] = regime_df['hurst']
                dataframe['adx'] = regime_df['adx']
                
                # 3. ML Predictions
                dataframe = self._calculate_ml_predictions(dataframe, metadata)

        except ImportError as e:
            logger.critical(f"Critical dependency missing in populate_indicators: {e}")
        except KeyError as e:
            logger.error(f"Missing column in populate_indicators: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in populate_indicators: {e}")
            
        return dataframe

    def _calculate_ml_predictions(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Calculate predictions using src.ml pipeline."""
        try:
            pair = metadata['pair']
            model, fe, feature_names = get_production_model(pair)
            
            if model and fe:
                # Feature Engineering
                df_fe = dataframe.copy()
                if 'date' in df_fe.columns and not isinstance(df_fe.index, pd.DatetimeIndex):
                    df_fe.set_index('date', inplace=True)
                
                # Transform (generate features + scale)
                # Note: This calls the refactored _apply_aggressive_cleaning which imputes NaNs
                X = fe.transform(df_fe)
                
                # Predict
                if hasattr(model, 'predict_proba'):
                    preds = model.predict_proba(X)[:, 1] # Probability of Class 1 (Buy/Long)
                else:
                    preds = model.predict(X)
                
                # Align predictions
                pred_series = pd.Series(preds, index=X.index)
                
                if isinstance(dataframe.index, pd.DatetimeIndex):
                    aligned_preds = pred_series.reindex(dataframe.index, fill_value=0.5)
                else:
                    if 'date' in dataframe.columns:
                        temp_df = dataframe.set_index('date')
                        aligned_preds = pred_series.reindex(temp_df.index, fill_value=0.5)
                        aligned_preds = aligned_preds.values
                    else:
                        if len(preds) < len(dataframe):
                            padding = np.full(len(dataframe) - len(preds), 0.5)
                            aligned_preds = np.concatenate([padding, preds])
                        else:
                            aligned_preds = preds[-len(dataframe):]

                dataframe['ml_prediction'] = aligned_preds
                
            else:
                dataframe['ml_prediction'] = 0.5
                
        except Exception as e:
            logger.warning(f"ML Prediction failed: {e}")
            dataframe['ml_prediction'] = 0.5
            
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Regime-Conditional Entry Logic using Core Logic Layer.
        """
        if USE_CUSTOM_MODULES:
            # Delegate to Core Logic which uses Regime Matrix
            df_signals = StoicLogic.populate_entry_exit_signals(
                dataframe, 
                buy_threshold=float(self.entry_prob_threshold.value),
                sell_rsi=int(self.sell_rsi.value)
            )
            
            dataframe['enter_long'] = df_signals['enter_long']
            
        else:
            dataframe['enter_long'] = 0
            
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Regime-Conditional Exits using Core Logic Layer."""
        if USE_CUSTOM_MODULES:
            # Delegate to Core Logic
            df_signals = StoicLogic.populate_entry_exit_signals(
                dataframe, 
                buy_threshold=float(self.entry_prob_threshold.value),
                sell_rsi=int(self.sell_rsi.value)
            )
            
            dataframe['exit_long'] = df_signals['exit_long']
        else:
            dataframe['exit_long'] = 0
            
        return dataframe
        
    def bot_start(self, **kwargs) -> None:
        """Initialize Risk Manager, Config, and Hybrid Connector."""
        if USE_CUSTOM_MODULES:
            try:
                from src.config.manager import ConfigurationManager
                ConfigurationManager.initialize()
                
                # Initialize parent classes
                super().bot_start(**kwargs)
                
                # Initialize Hybrid Connector
                # We need to know which pairs to monitor. 
                # Freqtrade doesn't give us the pairlist easily here, so we use config
                config = ConfigurationManager.get_config()
                pairs = config.pairs if hasattr(config, 'pairs') else ["BTC/USDT", "ETH/USDT"]
                
                self.initialize_hybrid_connector(pairs=pairs)
                
                logger.info("StoicRiskMixin, Configuration, and HybridConnector initialized")
            except Exception as e:
                logger.critical(f"Failed to initialize strategy components: {e}")
                raise

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, 
                           time_in_force: str, current_time: datetime, entry_tag: Optional[str], 
                           side: str, **kwargs) -> bool:
        """
        Override to use Risk Mixin validation AND Hybrid Connector safety checks.
        """
        if USE_CUSTOM_MODULES:
            # 1. Check Market Safety (Real-time MFT checks)
            if not self.check_market_safety(pair, side):
                return False
                
            # 2. Check Risk Limits (Portfolio Risk)
            return super().confirm_trade_entry(pair, order_type, amount, rate, time_in_force, 
                                             current_time, entry_tag, side, **kwargs)
        return True

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float], 
                           max_stake: float, leverage: float, entry_tag: Optional[str],
                           side: str, **kwargs) -> float:
        """
        Delegates sizing to StoicRiskMixin (Inverse Volatility Sizing).
        """
        if USE_CUSTOM_MODULES and self.risk_manager:
            return super().custom_stake_amount(pair, current_time, current_rate, proposed_stake,
                                             min_stake, max_stake, leverage, entry_tag, side, **kwargs)
        
        return proposed_stake

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                       current_rate: float, current_profit: float, **kwargs) -> float:
        """
        Volatility-Adjusted Stop Loss using Z-Score from Regime.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Base ATR stop
        atr = last_candle.get('atr', current_rate * 0.02)
        
        # Adjust multiplier based on Regime
        # If High Vol (Z > 1), widen stop to avoid noise
        vol_z = last_candle.get('vol_zscore', 0)
        
        base_mult = 2.0
        if vol_z > 1.0:
            base_mult = 3.0
        elif vol_z < -1.0:
            base_mult = 1.5
            
        stop_dist = atr * base_mult
        stop_pct = stop_dist / current_rate
        
        return -stop_pct
