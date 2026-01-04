#!/usr/bin/env python
"""
Reality Check Validation
=======================

Simplified validation script to verify system health on recent data.
"""

import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.training import (
    FeatureConfig,
    FeatureEngineer,
    TripleBarrierConfig,
    TripleBarrierLabeler,
)
from src.utils.logger import log as logger


def run_reality_check():
    logger.info("🕵️ Starting Reality Check on latest data...")

    # 1. Load latest data
    data_path = Path("user_data/data/binance/BTC_USDT-5m.feather")
    if not data_path.exists():
        logger.error(f"Data file not found at {data_path}")
        return

    df = pd.read_feather(data_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
    df = df.sort_index()

    # Take last 7 days
    latest_data = df.last("7D")
    logger.info(
        f"Analyzing data from {latest_data.index.min()} to {latest_data.index.max()} ({len(latest_data)} rows)"
    )

    # 2. Test Labeling (Triple Barrier)
    labeler = TripleBarrierLabeler(
        TripleBarrierConfig(take_profit=0.01, stop_loss=0.005, max_holding_period=24)
    )

    labels = labeler.label(latest_data)
    dist = labels.value_counts(dropna=False).to_dict()
    logger.info(f"Label distribution (7 days): {dist}")

    # 3. Test Feature Engineering
    engineer = FeatureEngineer(FeatureConfig(scale_features=True))
    features = engineer.fit_transform(latest_data)

    nan_count = features.isna().sum().sum()
    logger.info(f"Feature engineering complete. Total NaNs: {nan_count}")

    # 4. Result
    if dist.get(1.0, 0) > 0:
        logger.info("✅ SUCCESS: Found profitable opportunities in the last 7 days.")
    else:
        logger.warning(
            "⚠️ WARNING: No Buy signals (Label=1) found in the last 7 days with current thresholds."
        )

    logger.info("🚀 Reality Check Complete!")


if __name__ == "__main__":
    run_reality_check()
