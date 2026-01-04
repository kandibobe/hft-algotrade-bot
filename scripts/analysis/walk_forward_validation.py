#!/usr/bin/env python
"""
Walk-Forward Validation
=======================

The ONLY way to get realistic backtest results for trading strategies.
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.training import (
    FeatureConfig,
    FeatureEngineer,
    TripleBarrierConfig,
    TripleBarrierLabeler,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward validation."""

    # Data settings
    data_path: str = "user_data/data"
    pairs: list[str] = field(default_factory=lambda: ["BTC/USDT"])
    timeframe: str = "1h"

    # Window settings
    n_windows: int = 5  # Number of train/test windows
    train_ratio: float = 0.8  # 80% train, 20% test within each window

    # ML settings
    model_type: str = "lightgbm"
    optimize_hyperparams: bool = False  # Disable for faster runs

    # Labeling (tighter for 5m)
    take_profit_pct: float = 0.01
    stop_loss_pct: float = 0.005
    max_holding_period: int = 24

    # Output
    output_path: str = "user_data/walk_forward_results"


@dataclass
class WindowResult:
    """Results for a single walk-forward window."""

    window_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime

    # Metrics
    train_accuracy: float = 0.0
    test_accuracy: float = 0.0
    train_f1: float = 0.0
    test_f1: float = 0.0
    train_sharpe: float = 0.0
    test_sharpe: float = 0.0

    # Trade statistics
    n_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0


class WalkForwardValidator:
    """
    Walk-Forward Validation for trading strategies.
    """

    def __init__(self, config: WalkForwardConfig | None = None):
        """Initialize validator."""
        self.config = config or WalkForwardConfig()
        self.results: list[WindowResult] = []

    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Run walk-forward validation.
        """
        logger.info(f"Starting Walk-Forward Validation with {self.config.n_windows} windows")
        logger.info(f"Data range: {df.index.min()} to {df.index.max()}")

        # Create windows
        windows = self._create_windows(df)
        logger.info(f"Created {len(windows)} train/test windows")

        # Run each window
        self.results = []

        for window_id, (train_df, test_df) in enumerate(windows):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Window {window_id + 1}/{len(windows)}")
            logger.info(
                f"Train: {train_df.index.min()} to {train_df.index.max()} ({len(train_df)} samples)"
            )
            logger.info(
                f"Test:  {test_df.index.min()} to {test_df.index.max()} ({len(test_df)} samples)"
            )

            result = self._run_window(window_id, train_df, test_df)
            self.results.append(result)

            logger.info(f"Train Accuracy: {result.train_accuracy:.2%}")
            logger.info(f"Test Accuracy:  {result.test_accuracy:.2%}")
            logger.info(f"Test Sharpe:    {result.test_sharpe:.2f}")

        # Aggregate results
        aggregated = self._aggregate_results()

        logger.info(f"\n{'=' * 60}")
        logger.info("WALK-FORWARD VALIDATION COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info(f"Average Test Accuracy: {aggregated['avg_test_accuracy']:.2%}")
        logger.info(f"Average Test Sharpe:   {aggregated['avg_test_sharpe']:.2f}")

        # Save results
        self._save_results(aggregated)

        return aggregated

    def _create_windows(self, df: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create train/test windows for walk-forward validation.
        """
        n = len(df)
        window_size = n // self.config.n_windows

        windows = []

        for i in range(self.config.n_windows - 1):
            # Train window
            train_start = i * window_size
            train_end = (i + 1) * window_size

            # Test window (next segment)
            test_start = train_end
            test_end = min((i + 2) * window_size, n)

            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()

            windows.append((train_df, test_df))

        return windows

    def _run_window(
        self, window_id: int, train_df: pd.DataFrame, test_df: pd.DataFrame
    ) -> WindowResult:
        """
        Run training and testing for a single window.
        """
        result = WindowResult(
            window_id=window_id,
            train_start=train_df.index.min(),
            train_end=train_df.index.max(),
            test_start=test_df.index.min(),
            test_end=test_df.index.max(),
        )

        try:
            # 1. Create labels with Triple Barrier
            labeler = TripleBarrierLabeler(
                TripleBarrierConfig(
                    take_profit=self.config.take_profit_pct,
                    stop_loss=self.config.stop_loss_pct,
                    max_holding_period=self.config.max_holding_period,
                    include_hold_class=False,  # FORCE BINARY FOR CLASSIFIER
                )
            )

            train_labels = labeler.label(train_df)
            test_labels = labeler.label(test_df)

            train_df["label"] = train_labels
            test_df["label"] = test_labels

            # 2. Feature engineering
            engineer = FeatureEngineer(
                FeatureConfig(
                    scale_features=True,
                    scaling_method="standard",
                )
            )

            train_features = engineer.fit_transform(train_df)
            test_features = engineer.transform(test_df)

            # 3. Prepare X, y
            feature_cols = engineer.get_feature_names()

            # Robust filtering
            train_clean = train_features.dropna(subset=["label"])
            train_clean = train_clean[train_clean["label"] != 0]

            test_clean = test_features.dropna(subset=["label"])
            test_clean = test_clean[test_clean["label"] != 0]

            X_train = train_clean[feature_cols]
            y_train = (train_clean["label"] == 1).astype(int)

            X_test = test_clean[feature_cols]
            y_test = (test_clean["label"] == 1).astype(int)

            if len(X_train) < 100 or len(X_test) < 10:
                logger.warning(f"Window {window_id}: Insufficient data after cleaning")
                return result

            # 4. Train model (using LightGBM)
            from lightgbm import LGBMClassifier

            model = LGBMClassifier(
                n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1
            )
            model.fit(X_train, y_train)

            # Calculate dummy train metrics
            train_accuracy = model.score(X_train, y_train)

            # 5. Evaluate on test
            test_predictions = model.predict(X_test)

            # Calculate metrics
            from sklearn.metrics import accuracy_score, f1_score

            result.train_accuracy = train_accuracy
            result.test_accuracy = accuracy_score(y_test, test_predictions)
            result.test_f1 = f1_score(y_test, test_predictions, average="weighted")

            # 6. Calculate trading metrics
            trade_metrics = self._calculate_trading_metrics(
                test_df.loc[test_clean.index], y_test, test_predictions
            )
            result.n_trades = trade_metrics["n_trades"]
            result.win_rate = trade_metrics["win_rate"]
            result.profit_factor = trade_metrics["profit_factor"]
            result.total_return = trade_metrics["total_return"]
            result.max_drawdown = trade_metrics["max_drawdown"]
            result.test_sharpe = trade_metrics["sharpe"]

        except Exception as e:
            logger.error(f"Window {window_id} failed: {e}")

        return result

    def _calculate_trading_metrics(
        self, df: pd.DataFrame, y_true: pd.Series, y_pred: np.ndarray
    ) -> dict[str, float]:
        """
        Calculate trading performance metrics.
        """
        # Simulate trades based on predictions
        returns = df["close"].pct_change()

        # Strategy returns: long when pred=1, flat otherwise
        strategy_returns = returns * (y_pred == 1)
        strategy_returns = strategy_returns.dropna()

        if len(strategy_returns) == 0:
            return {
                "n_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
            }

        n_trades = (y_pred == 1).sum()
        winning_trades = strategy_returns[strategy_returns > 0]
        losing_trades = strategy_returns[strategy_returns < 0]
        win_rate = len(winning_trades) / max(1, len(winning_trades) + len(losing_trades))
        profit_factor = winning_trades.sum() / max(0.0001, abs(losing_trades.sum()))
        total_return = (1 + strategy_returns).prod() - 1

        cumulative = (1 + strategy_returns).cumprod()
        drawdown = (cumulative - cumulative.expanding().max()) / cumulative.expanding().max()
        max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0

        if strategy_returns.std() > 0:
            sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(365 * 24 * 12)
        else:
            sharpe = 0.0

        return {
            "n_trades": n_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "sharpe": sharpe,
        }

    def _aggregate_results(self) -> dict[str, Any]:
        """Aggregate results across all windows."""
        if not self.results:
            return {}
        test_accuracies = [r.test_accuracy for r in self.results if r.test_accuracy > 0]
        test_sharpes = [r.test_sharpe for r in self.results]
        test_returns = [r.total_return for r in self.results]
        if not test_accuracies:
            return {"avg_test_accuracy": 0, "avg_test_sharpe": 0, "total_return": 0}
        return {
            "avg_test_accuracy": np.mean(test_accuracies),
            "avg_test_sharpe": np.mean(test_sharpes),
            "total_return": np.prod([1 + r for r in test_returns]) - 1,
            "n_windows": len(self.results),
        }

    def _save_results(self, results: dict[str, Any]) -> None:
        """Save results to file."""
        output_dir = Path(self.config.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"walk_forward_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")

    def generate_report(self) -> str:
        """Generate human-readable report."""
        if not self.results:
            return "No results to report"
        report = ["=" * 70, "WALK-FORWARD VALIDATION REPORT", "=" * 70]
        agg = self._aggregate_results()
        report.append(f"  Average Test Accuracy:  {agg['avg_test_accuracy']:.2%}")
        report.append(f"  Average Test Sharpe:    {agg['avg_test_sharpe']:.2f}")
        report.append(f"  Combined Return:        {agg['total_return']:.2%}")
        report.append("=" * 70)
        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Walk-Forward Validation")
    parser.add_argument("--pairs", nargs="+", default=["BTC/USDT"])
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--windows", type=int, default=3)
    parser.add_argument("--data-path", default="user_data/data")
    args = parser.parse_args()

    pair = args.pairs[0].replace("/", "_")
    path = Path(args.data_path) / "binance" / f"{pair}-{args.timeframe}.feather"

    if not path.exists():
        logger.error(f"No data found at {path}")
        sys.exit(1)

    df = pd.read_feather(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
    df = df.sort_index()

    config = WalkForwardConfig(
        pairs=args.pairs, timeframe=args.timeframe, n_windows=args.windows, data_path=args.data_path
    )
    validator = WalkForwardValidator(config)
    results = validator.run(df)
    print(validator.generate_report())


if __name__ == "__main__":
    main()
