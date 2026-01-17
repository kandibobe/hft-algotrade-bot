"""
HRP Portfolio Stress Test Utility
=================================

Simulates HRP performance during extreme market regimes.
"""

import logging
import pandas as pd
import numpy as np
from src.risk.hrp import get_hrp_weights
from src.utils.regime_detection import calculate_regime, MarketRegime

logger = logging.getLogger(__name__)

def run_hrp_stress_test(prices_df: pd.DataFrame):
    """
    Stress test HRP weights across different market regimes.
    """
    logger.info("Starting HRP Stress Test...")
    
    # Identify regimes for each asset (using first as proxy for market)
    proxy_asset = prices_df.columns[0]
    regimes = calculate_regime(
        high=prices_df[proxy_asset], # Simplified
        low=prices_df[proxy_asset], 
        close=prices_df[proxy_asset], 
        volume=pd.Series(1, index=prices_df.index)
    )
    
    results = {}
    
    for regime_name in MarketRegime:
        mask = regimes['regime'] == regime_name.value
        if mask.any():
            regime_prices = prices_df[mask]
            if len(regime_prices) > 20:
                weights = get_hrp_weights(regime_prices)
                results[regime_name.value] = {
                    "avg_weight": np.mean(list(weights.values())),
                    "std_weight": np.std(list(weights.values())),
                    "max_weight": np.max(list(weights.values())),
                    "min_weight": np.min(list(weights.values()))
                }
                logger.info(f"Regime {regime_name.value}: HRP Stability Metrics calculated.")
                
    return results

if __name__ == "__main__":
    # Example usage with mock data
    dates = pd.date_range("2025-01-01", periods=500, freq="1h")
    data = pd.DataFrame({
        "BTC": np.exp(np.random.normal(0.0001, 0.02, 500).cumsum()),
        "ETH": np.exp(np.random.normal(0.0001, 0.03, 500).cumsum())
    }, index=dates)
    print(run_hrp_stress_test(data))
