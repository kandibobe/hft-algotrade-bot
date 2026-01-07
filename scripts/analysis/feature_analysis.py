
import logging
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.training.feature_engineering import FeatureEngineer, FeatureConfig

def analyze_feature_predictiveness():
    """
    Analyzes the predictive power of generated features on future returns.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 1. Load Data
        logging.info("Loading data...")
        df = pd.read_feather("user_data/data/binance/BTC_USDT-1h.feather")
        
        # 2. Generate Features
        logging.info("Generating features...")
        # Use a config that generates all features, but does not scale or enforce stationarity yet
        config = FeatureConfig(enforce_stationarity=False) 
        engineer = FeatureEngineer(config)
        features_df = engineer.prepare_data(df.copy(), use_cache=False)

        # 3. Calculate Future Returns (Target)
        logging.info("Calculating future returns...")
        future_periods = [1, 3, 5, 10, 20] # Predict 1h, 3h, 5h, 10h, 20h returns
        for period in future_periods:
            features_df[f'future_return_{period}h'] = features_df['close'].shift(-period) / features_df['close'] - 1

        # Drop rows with NaNs created by future returns calculation
        features_df.dropna(inplace=True)
        
        # 4. Calculate Correlations
        logging.info("Calculating correlations...")
        
        # Identify feature columns (exclude OHLCV and future returns)
        feature_columns = [col for col in features_df.columns if not col.startswith('future_return_') and col not in ['open', 'high', 'low', 'close', 'volume', 'date']]
        
        correlations = {}
        for period in future_periods:
            target_col = f'future_return_{period}h'
            corrs = features_df[feature_columns].corrwith(features_df[target_col])
            correlations[target_col] = corrs.abs().sort_values(ascending=False)
            
        # 5. Display Results
        for period, corrs in correlations.items():
            print(f"\n--- Top 10 Predictive Features for {period} ---")
            print(corrs.head(10))

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_feature_predictiveness()
