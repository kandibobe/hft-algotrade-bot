"""
Stoic Citadel - Market Regime Detection
========================================

Detect market regimes (trending/ranging, high/low volatility)
to adapt strategy behavior.

"The wise trader adapts to market conditions."
"""

import logging
from enum import Enum
from typing import Dict, Literal, Optional

import numpy as np
import pandas as pd
from .math_tools import calculate_hurst

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types."""

    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    RANDOM_WALK = "random_walk"


def detect_trend_regime(
    close: pd.Series,
    ema_short: int = 50,
    ema_long: int = 200,
    adx_threshold: float = 25.0,
    high: Optional[pd.Series] = None,
    low: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Detect market trend regime using EMA crossover and ADX strength.
    """
    from .indicators import calculate_adx, calculate_ema

    # Calculate EMAs
    ema_s = calculate_ema(close, ema_short)
    ema_l = calculate_ema(close, ema_long)

    # Calculate ADX if high/low provided
    if high is not None and low is not None:
        adx_data = calculate_adx(high, low, close)
        adx = adx_data["adx"]
        is_trending = adx > adx_threshold
    else:
        # Fallback: use EMA slope as trend indicator
        ema_slope = ema_l.diff(5) / ema_l * 100
        is_trending = ema_slope.abs() > 0.1

    # Determine regime
    regime = pd.Series(index=close.index, dtype=str)

    bull_trend = (ema_s > ema_l) & is_trending
    bear_trend = (ema_s < ema_l) & is_trending
    ranging = ~is_trending

    regime[bull_trend] = MarketRegime.TRENDING_BULL.value
    regime[bear_trend] = MarketRegime.TRENDING_BEAR.value
    regime[ranging] = MarketRegime.RANGING.value

    return regime


def detect_volatility_regime(
    close: pd.Series,
    lookback: int = 30,
    high_vol_percentile: float = 75,
    low_vol_percentile: float = 25,
) -> pd.Series:
    """
    Detect volatility regime based on historical realized volatility distribution.
    """
    # Calculate rolling realized volatility
    returns = close.pct_change()
    realized_vol = returns.rolling(window=lookback).std() * np.sqrt(252)

    # Calculate rolling percentiles
    vol_rank = realized_vol.rolling(window=lookback * 5).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False
    )

    # Classify
    regime = pd.Series(index=close.index, dtype=str)

    high_vol = vol_rank > high_vol_percentile
    low_vol = vol_rank < low_vol_percentile
    normal_vol = ~high_vol & ~low_vol

    regime[high_vol] = MarketRegime.HIGH_VOLATILITY.value
    regime[low_vol] = MarketRegime.LOW_VOLATILITY.value
    regime[normal_vol] = "normal_volatility"

    return regime


def calculate_regime_score(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
) -> pd.DataFrame:
    """
    Calculate comprehensive regime scores (V5 Enhanced).

    Returns DataFrame with multiple regime indicators including Hurst and Volatility Rank.

    Args:
        high: High price series
        low: Low price series
        close: Close price series
        volume: Volume series

    Returns:
        DataFrame with regime scores and indicators
    """
    from .indicators import calculate_adx, calculate_atr, calculate_rsi

    result = pd.DataFrame(index=close.index)

    # 1. Volatility Rank (Normalized ATR)
    # We use a long window (500) to get a statistically significant rank
    atr = calculate_atr(high, low, close, 14)
    atr_pct = atr / close
    
    # Percentile Rank of ATR% over last 500 candles
    result["volatility_rank"] = (
        atr_pct
        .rolling(window=500, min_periods=100)
        .rank(pct=True)
    )
    
    # 2. Hurst Exponent (Trend Persistence)
    # Window 100 is standard for daily/hourly
    result["hurst"] = calculate_hurst(close, window=100)
    
    # 3. Liquidity (Relative Volume)
    vol_sma = volume.rolling(20).mean()
    result["rel_volume"] = volume / vol_sma.replace(0, 1)

    # 4. Backward Compatibility Scores (Legacy V4 support)
    ema_50 = close.ewm(span=50).mean()
    ema_200 = close.ewm(span=200).mean()
    result["ema_trend"] = (ema_50 > ema_200).astype(int)
    
    adx_data = calculate_adx(high, low, close)
    result["adx"] = adx_data["adx"]
    result["rsi"] = calculate_rsi(close)
    
    # Composite Score (Legacy)
    result["regime_score"] = (
        result["ema_trend"] * 30
        + ((close > ema_50).astype(int)) * 20
        + (result["rsi"] > 50).astype(int) * 20
        + (result["adx"] > 25).astype(int) * 15
        + (result["rel_volume"] > 1).astype(int) * 15
    )

    # 5. Risk Factor (Advanced V5)
    # Scale risk based on Volatility Rank (Inverse Volatility Sizing)
    # If Vol Rank is 0.9 (High Risk), factor -> 0.6
    # If Vol Rank is 0.1 (Low Risk), factor -> 1.4
    # Formula: 1.5 - VolRank (clipped to 0.5-1.5)
    result["risk_factor"] = (1.5 - result["volatility_rank"]).clip(0.5, 1.5)

    return result


def get_regime_parameters(
    regime_score: float, base_risk: float = 0.02, base_leverage: float = 1.0
) -> Dict[str, float]:
    """
    Get recommended trading parameters based on regime (Legacy V4 wrapper).
    """
    if regime_score > 70:
        return {
            "risk_per_trade": base_risk * 1.2,
            "leverage": min(base_leverage * 1.5, 3.0),
            "mode": "aggressive",
        }
    elif regime_score > 40:
        return {
            "risk_per_trade": base_risk,
            "leverage": base_leverage,
            "mode": "normal",
        }
    else:
        return {
            "risk_per_trade": base_risk * 0.5,
            "leverage": base_leverage * 0.5,
            "mode": "defensive",
        }
