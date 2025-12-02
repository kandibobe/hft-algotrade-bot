"""
Simple Test Strategy - Minimal Working Example
==============================================

Basic RSI strategy for testing infrastructure.
No complex dependencies - just works.

Author: Stoic Citadel
Version: 1.0.0
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class SimpleTestStrategy(IStrategy):
    """
    Ultra-simple strategy for testing.
    Buy when RSI < 30, Sell when RSI > 70.
    """

    INTERFACE_VERSION = 3
    
    # Basic settings
    timeframe = '5m'
    startup_candle_count = 50
    can_short = False
    
    # Simple ROI
    minimal_roi = {
        "0": 0.05,   # 5%
        "30": 0.03,  # 3% after 150 min
        "60": 0.01   # 1% after 300 min
    }
    
    # Stoploss
    stoploss = -0.05  # -5%
    
    # Trailing stop
    trailing_stop = False
    
    # Exit signal
    use_exit_signal = True
    exit_profit_only = False
    
    # Process only new candles
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Calculate RSI only."""
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Buy when RSI < 30."""
        dataframe.loc[
            (dataframe['rsi'] < 30),
            'enter_long'
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Sell when RSI > 70."""
        dataframe.loc[
            (dataframe['rsi'] > 70),
            'exit_long'
        ] = 1
        return dataframe
