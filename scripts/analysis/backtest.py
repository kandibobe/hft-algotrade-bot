#!/usr/bin/env python3
"""
Simple Backtest Script (Fixed)
==============================

Corrected backtest script that:
1. Splits data into Train/Test sets (NO Lookahead)
2. Trains an ML model on Train set
3. Backtests on Test set using Event-Driven Logic
4. Includes Fees & Slippage

Usage:
    python scripts/backtest.py --symbol BTC/USDT --timeframe 5m --start 2024-01-01 --end 2024-12-31
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.wfo_engine import BacktestConfig, VectorizedBacktester
from src.ml.training.feature_engineering import FeatureConfig, FeatureEngineer
from src.ml.training.labeling import TripleBarrierConfig, TripleBarrierLabeler
from src.ml.training.model_trainer import ModelTrainer, TrainingConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_synthetic_data(start, end, timeframe):
    """Load synthetic data for testing."""
    # Fix pandas freq
    freq = timeframe
    if timeframe.endswith("m") and "min" not in timeframe:
        freq = timeframe.replace("m", "min")

    dates = pd.date_range(start, end, freq=freq)
    n = len(dates)
    np.random.seed(42)
    returns = np.random.randn(n) * 0.002  # 0.2% volatility
    prices = 50000 * np.exp(np.cumsum(returns))

    data = pd.DataFrame(
        {
            "open": prices,
            "high": prices * 1.001,
            "low": prices * 0.999,
            "close": prices,
            "volume": np.random.uniform(100, 1000, n),
        },
        index=dates,
    )
    return data


def main():
    parser = argparse.ArgumentParser(description="Run rigorous backtest")
    parser.add_argument("--symbol", type=str, default="BTC/USDT")
    parser.add_argument("--start", type=str, default="2024-01-01")
    parser.add_argument("--end", type=str, default="2024-02-01")
    parser.add_argument("--timeframe", type=str, default="5m")
    args = parser.parse_args()

    logger.info("Starting Rigorous Backtest...")

    # 1. Load Data
    try:
        from src.data.loader import DataLoader

        loader = DataLoader()
        data = loader.load_data(args.symbol, args.timeframe, args.start, args.end)
    except Exception:
        logger.warning("Could not load real data, using synthetic data")
        data = load_synthetic_data(args.start, args.end, args.timeframe)

    # 2. Split Train/Test (No Lookahead)
    split_idx = int(len(data) * 0.7)
    train_data = data.iloc[:split_idx]
    test_data = data.iloc[split_idx:]

    logger.info(f"Total data: {len(data)}")
    logger.info(f"Train: {len(train_data)} candles, Test: {len(test_data)} candles")

    if len(train_data) < 500:
        logger.error("Insufficient training data! Need at least 500 candles.")
        return

    # 3. Labeling
    labeler_config = TripleBarrierConfig(take_profit=0.015, stop_loss=0.0075, max_holding_period=24)
    labeler = TripleBarrierLabeler(labeler_config)

    logger.info("Generating labels...")
    train_labels = labeler.label(train_data)
    # Convert to binary
    train_labels = train_labels.replace({-1: 0, 1: 1})

    # 4. Feature Engineering
    fe_config = FeatureConfig(scale_features=True)
    fe = FeatureEngineer(fe_config)

    logger.info("Engineering features...")
    X_train = fe.fit_transform(train_data)
    X_test = fe.transform(test_data)

    # Align X and y
    common_idx = X_train.index.intersection(train_labels.index)
    X_train = X_train.loc[common_idx]
    y_train = train_labels.loc[common_idx].dropna()
    X_train = X_train.loc[y_train.index]

    # 5. Train Model
    logger.info("Training model...")
    # Use random_forest as it is always available (sklearn)
    # Disable internal feature selection to ensure X_test columns match model expectation
    trainer = ModelTrainer(TrainingConfig(model_type="random_forest", feature_selection=False))
    model, _ = trainer.train(X_train, y_train)

    # 6. Predict on Test
    logger.info("Predicting on Test Set...")
    probs = model.predict_proba(X_test)
    if probs.shape[1] > 1:
        probs = probs[:, 1]

    # Generate Signals
    threshold = 0.65
    signals = pd.Series((probs > threshold).astype(int), index=X_test.index)

    # 7. Run Vectorized Backtest
    logger.info("Running Event-Driven Backtest...")
    bt_config = BacktestConfig(
        initial_capital=10000,
        fee_rate=0.001,
        slippage_rate=0.0005,
        take_profit=0.015,
        stop_loss=0.0075,
        max_holding_bars=24,
    )
    backtester = VectorizedBacktester(bt_config)
    results = backtester.run(signals, test_data)

    # 8. Report
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS (Test Set Only)")
    print("=" * 50)
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Final Capital: ${results['final_capital']:.2f}")

    trades = results["trades"]
    if len(trades) > 0:
        win_rate = (trades["net_pnl"] > 0).mean()
        print(f"Trades: {len(trades)}")
        print(f"Win Rate: {win_rate:.2%}")
        print(f"Avg Net PnL: ${trades['net_pnl'].mean():.2f}")
    else:
        print("No trades executed.")

    print("=" * 50)


if __name__ == "__main__":
    main()
