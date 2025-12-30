"""
Stoic Citadel - Mathematical Tools
==================================

Advanced mathematical functions for financial analysis.
Focuses on statistical measures of series properties (Hurst, Entropy, etc.).
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Try to import Numba for performance
try:
    from numba import jit, float64, int64
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False
    # Dummy decorator if Numba is not present
    def jit(signature_or_function=None, nopython=True, **kwargs):
        def decorator(func):
            return func
        if callable(signature_or_function):
            return signature_or_function
        return decorator
    float64 = None

def _calculate_rs_hurst_numpy(prices):
    """
    Numpy implementation of R/S Hurst (slower but works without Numba).
    """
    n = len(prices)
    if n < 10:
        return 0.5
        
    # Calculate returns
    returns = np.diff(np.log(prices))
    
    mean_ret = np.mean(returns)
    deviations = returns - mean_ret
    cumsum_deviations = np.cumsum(deviations)
    
    R = np.max(cumsum_deviations) - np.min(cumsum_deviations)
    S = np.std(returns)
    
    if S == 0 or R == 0:
        return 0.5
        
    rs = R / S
    h = np.log(rs) / np.log(n)
    
    return h

if HAVE_NUMBA:
    @jit(float64(float64[:]), nopython=True)
    def _calculate_rs_hurst_numba(prices):
        n = len(prices)
        if n < 10:
            return 0.5
            
        returns = np.diff(np.log(prices))
        
        mean_ret = np.mean(returns)
        deviations = returns - mean_ret
        cumsum_deviations = np.cumsum(deviations)
        
        R = np.max(cumsum_deviations) - np.min(cumsum_deviations)
        S = np.std(returns)
        
        if S == 0 or R == 0:
            return 0.5
            
        rs = R / S
        h = np.log(rs) / np.log(n)
        
        return h

    @jit(float64[:](float64[:], int64), nopython=True)
    def _rolling_hurst_loop(values, window):
        n = len(values)
        result = np.full(n, np.nan)
        
        for i in range(window, n):
            window_slice = values[i-window:i]
            result[i] = _calculate_rs_hurst_numba(window_slice)
            
        return result
else:
    def _rolling_hurst_loop(values, window):
        n = len(values)
        result = np.full(n, np.nan)
        
        for i in range(window, n):
            window_slice = values[i-window:i]
            result[i] = _calculate_rs_hurst_numpy(window_slice)
            
        return result

def calculate_hurst(series: pd.Series, window: int = 100) -> pd.Series:
    """
    Calculate rolling Hurst Exponent (R/S analysis).
    Automatically falls back to NumPy if Numba is not available.
    """
    values = series.values.astype(np.float64)
    
    result = _rolling_hurst_loop(values, window)
    
    return pd.Series(result, index=series.index)

def calculate_efficiency_ratio(series: pd.Series, window: int = 100) -> pd.Series:
    """
    Calculate Kaufman's Efficiency Ratio (ER).
    ER = |Change| / Sum(Abs(Changes))
    """
    change = series.diff(window).abs()
    volatility = series.diff().abs().rolling(window).sum()
    er = change / volatility
    return er.fillna(0)

def calculate_rolling_hurst(series: pd.Series, window: int = 100) -> pd.Series:
    """Wrapper for backward compatibility."""
    return calculate_hurst(series, window)
