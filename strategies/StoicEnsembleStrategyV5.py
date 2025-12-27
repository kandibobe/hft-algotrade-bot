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
Version: 5.1.0 (Refactored Logic)
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
    from src.utils.indicators import (
        calculate_ema, calculate_rsi, calculate_macd,
        calculate_atr, calculate_bollinger_bands,
        calculate_stochastic, calculate_adx, calculate_obv
    )
    from src.utils.regime_detection import calculate_regime_score, get_regime_parameters
    # We still use V4's ML integration helper functions if we want to keep ML
    from user_data.strategies.StoicEnsembleStrategyV4 import get_cached_model_and_fe
    # Import Risk Mixin
    from user_data.strategies.StoicRiskMixin import StoicRiskMixin
    # Import Core Logic
    from src.strategies.core_logic import StoicLogic
    USE_CUSTOM_MODULES = True
except ImportError as e:
    USE_CUSTOM_MODULES = False
    import talib.abstract as ta
    logging.getLogger(__name__).warning(f"Custom modules not available: {e}")
    # Dummy mixin if import fails
    class StoicRiskMixin: pass
    class StoicLogic: pass

logger = logging.getLogger(__name__)

class StoicEnsembleStrategyV5(IStrategy, StoicRiskMixin):
    INTERFACE_VERSION = 3

    # Hyperparameters
    # Buy Params
    buy_rsi = IntParameter(20, 40, default=30, space="buy")
    buy_adx = IntParameter(15, 30, default=20, space="buy")
    buy_hurst_min_trend = DecimalParameter(0.55, 0.65, default=0.60, space="buy")
    buy_hurst_max_meanrev = DecimalParameter(0.35, 0.45, default=0.40, space="buy")
    
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
            # 1. Standard Indicators
            if USE_CUSTOM_MODULES:
                dataframe = self._populate_indicators_custom(dataframe)
            else:
                # Fallback implementation omitted for brevity in V5 proof-of-concept
                pass

            # 2. ML Predictions (Reuse V4 logic)
            dataframe = self._calculate_ml_predictions(dataframe, metadata)

            # 3. Regime Detection (V5)
            # This adds 'volatility_rank', 'hurst', 'risk_factor'
            if USE_CUSTOM_MODULES:
                regime_df = calculate_regime_score(
                    dataframe['high'], dataframe['low'], dataframe['close'], dataframe['volume']
                )
                # Merge safely
                for col in regime_df.columns:
                    dataframe[col] = regime_df[col]

        except Exception as e:
            logger.error(f"Error in indicators: {e}")
            
        return dataframe

    def _populate_indicators_custom(self, dataframe: DataFrame) -> DataFrame:
        # Basic needed for logic
        dataframe['ema_50'] = calculate_ema(dataframe['close'], 50)
        dataframe['ema_200'] = calculate_ema(dataframe['close'], 200)
        dataframe['rsi'] = calculate_rsi(dataframe['close'], 14)
        
        bb = calculate_bollinger_bands(dataframe['close'], 20, 2.0)
        dataframe['bb_lower'] = bb['lower']
        dataframe['bb_upper'] = bb['upper']
        dataframe['bb_width'] = bb['width']
        
        dataframe['atr'] = calculate_atr(dataframe['high'], dataframe['low'], dataframe['close'], 14)
        
        return dataframe

    def _calculate_ml_predictions(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Reuse V4 ML logic."""
        # Simplified copy of V4 ML logic
        try:
            from user_data.strategies.StoicEnsembleStrategyV4 import get_cached_model_and_fe
            # We can instantiate V4 just to use its helper if needed, but methods are instance methods.
            # Instead, we reimplement simpler version calling the global helper.
            pair = metadata['pair']
            model, fe = get_cached_model_and_fe(pair, Path("."))
            
            if model and fe:
                df_fe = dataframe.copy()
                if 'date' in df_fe.columns: df_fe.set_index('date', inplace=True)
                
                # Use transform (which assumes fit was done on train data)
                X = fe.transform(df_fe)
                
                # Align features
                if hasattr(model, 'feature_names_in_'):
                    # Ensure all features exist, fill with 0 only if strictly necessary
                    # but better to let it fail or warn if features missing
                    X = X.reindex(columns=model.feature_names_in_, fill_value=0)
                
                if hasattr(model, 'predict_proba'):
                    preds = model.predict_proba(X)[:, 1] # Class 1
                else:
                    preds = model.predict(X)
                
                # Map back
                # Handle alignment if dataframe length != preds length (e.g. startup candles dropped)
                # But here we pass full dataframe to FE, so lengths should match roughly
                # However, rolling windows in FE might drop initial rows
                if len(preds) < len(dataframe):
                    # Pad with 0.5 at the beginning
                    padding = np.full(len(dataframe) - len(preds), 0.5)
                    preds = np.concatenate([padding, preds])
                
                dataframe['ml_prediction'] = preds
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
            # Delegate to Core Logic
            df_signals = StoicLogic.populate_entry_exit_signals(
                dataframe, 
                buy_threshold=float(self.entry_prob_threshold.value),
                sell_rsi=int(self.sell_rsi.value)
            )
            
            # Map back signals
            dataframe['enter_long'] = df_signals['enter_long']
            
        else:
            # Fallback (should not happen in prod)
            dataframe['enter_long'] = 0
            
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Regime-Conditional Exits using Core Logic Layer."""
        if USE_CUSTOM_MODULES:
            # Delegate to Core Logic
            # Note: We re-calculate signals here which is redundant but safe
            # Optimization: could cache or merge in populate_entry_trend
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
        """Initialize Risk Manager."""
        if USE_CUSTOM_MODULES:
            super().bot_start(**kwargs)
            logger.info("StoicRiskMixin initialized from Strategy")

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, 
                           time_in_force: str, current_time: datetime, entry_tag: Optional[str], 
                           side: str, **kwargs) -> bool:
        """
        Override to use Risk Mixin validation.
        """
        if USE_CUSTOM_MODULES:
            return super().confirm_trade_entry(pair, order_type, amount, rate, time_in_force, 
                                             current_time, entry_tag, side, **kwargs)
        return True

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float], 
                           max_stake: float, leverage: float, entry_tag: Optional[str],
                           side: str, **kwargs) -> float:
        """
        Delegates sizing to StoicRiskMixin -> RiskManager.
        """
        if USE_CUSTOM_MODULES and self.risk_manager:
            return super().custom_stake_amount(pair, current_time, current_rate, proposed_stake,
                                             min_stake, max_stake, leverage, entry_tag, side, **kwargs)
        
        # Fallback
        return proposed_stake

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                       current_rate: float, current_profit: float, **kwargs) -> float:
        """
        Volatility-Adjusted Stop Loss.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Base ATR stop
        atr = last_candle.get('atr', current_rate * 0.02)
        vol_rank = last_candle.get('volatility_rank', 0.5)
        
        # Dynamic Multiplier
        mult = 2.0 + vol_rank  # Maps 0.0->2.0, 1.0->3.0
        
        stop_dist = atr * mult
        stop_pct = stop_dist / current_rate
        
        return -stop_pct
