"""
Stoic Citadel - Core Trading Logic
==================================

Pure logic layer for trading decisions.
Decoupled from Freqtrade to allow independent testing and simulation.
Supports both scalar (unit test) and vectorized (backtest) operations.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
import pandas as pd
import numpy as np

@dataclass
class TradeDecision:
    should_enter_long: bool = False
    should_exit_long: bool = False
    reason: str = ""

class StoicLogic:
    """
    Encapsulates the core decision making logic.
    """
    
    @staticmethod
    def populate_entry_exit_signals(dataframe: pd.DataFrame, 
                                  buy_threshold: float = 0.6,
                                  sell_rsi: int = 75) -> pd.DataFrame:
        """
        Vectorized signal generation.
        Returns dataframe with 'enter_long' and 'exit_long' columns.
        """
        df = dataframe.copy()
        df['enter_long'] = 0
        df['exit_long'] = 0
        
        # Ensure required columns exist
        required = ['hurst', 'rsi', 'close', 'bb_lower', 'ema_200', 'ml_prediction', 'volume']
        for col in required:
            if col not in df.columns:
                # If missing, we can't trade safely. Return empty signals.
                return df

        # --- Entry Logic ---
        
        # 1. Random Walk Filter (Kill Zone: 0.45 < H < 0.55)
        # We don't need to explicitly filter if we only select strictly > 0.6 or < 0.4
        
        # 2. Trending Regime (H > 0.6)
        trend_cond = (
            (df['hurst'] > 0.6) &
            (df['close'] > df['ema_200']) &
            (df['ml_prediction'] > buy_threshold) &
            (df['volume'] > 0)
        )
        
        # 3. Mean Reversion Regime (H < 0.4)
        mean_rev_cond = (
            (df['hurst'] < 0.4) &
            (df['rsi'] < 30) &
            (df['close'] <= df['bb_lower'])
        )
        
        # Combine
        df.loc[trend_cond | mean_rev_cond, 'enter_long'] = 1
        
        # --- Exit Logic ---
        exit_cond = (df['rsi'] > sell_rsi)
        df.loc[exit_cond, 'exit_long'] = 1
        
        return df

    @staticmethod
    def get_entry_decision(candle: Dict[str, Any], threshold: float = 0.6) -> TradeDecision:
        """
        Scalar version for unit testing or event-driven execution.
        """
        # Extract features with safe defaults
        hurst = candle.get('hurst', 0.5)
        rsi = candle.get('rsi', 50)
        close = candle.get('close', 0)
        bb_lower = candle.get('bb_lower', 0)
        ema_200 = candle.get('ema_200', 0)
        ml_pred = candle.get('ml_prediction', 0.5)
        volume = candle.get('volume', 0)
        
        # 2. Trending Regime (H > 0.6)
        if hurst > 0.6:
            if (close > ema_200) and (ml_pred > threshold) and (volume > 0):
                return TradeDecision(True, False, "Trend Follow")
                
        # 3. Mean Reversion Regime (H < 0.4)
        if hurst < 0.4:
            if (rsi < 30) and (close <= bb_lower):
                return TradeDecision(True, False, "Mean Reversion")
                    
        return TradeDecision(False, False)
