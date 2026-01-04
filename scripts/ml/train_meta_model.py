#!/usr/bin/env python3
"""
Meta-Model Training Script
==========================

Implements De Prado's Meta-Labeling technique:
1. Train a Primary Model (High Recall, Low Precision)
2. Generate predictions on training set
3. Create Meta-Labels: 1 if Primary was correct, 0 if wrong
4. Train Secondary Model (Meta-Model) to filter Primary signals

Usage:
    python scripts/train_meta_model.py --pair BTC/USDT
"""

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.training.advanced_pipeline import (
    AdvancedFeatureEngineer,
    DataPreprocessor,
    TripleBarrierWithPurging,
)

try:
    import xgboost as xgb

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


class MetaModelTrainer:
    def __init__(
        self, data_dir: str = "user_data/data/binance", models_dir: str = "user_data/models"
    ):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.preprocessor = DataPreprocessor()
        self.engineer = AdvancedFeatureEngineer()
        self.labeler = TripleBarrierWithPurging()

    def load_data(self, pair: str, timeframe: str = "5m") -> pd.DataFrame:
        """Load data from feather/parquet."""
        pair_filename = pair.replace("/", "_")
        path = self.data_dir / f"{pair_filename}-{timeframe}.feather"

        if not path.exists():
            raise FileNotFoundError(f"Data not found: {path}")

        print(f"Loading {path}...")
        df = pd.read_feather(path)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

        return df.sort_index()

    def train_primary_model(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """Train primary model (Optimized for Recall)."""
        print("\n🤖 Training Primary Model (High Recall)...")

        # Use simple RandomForest for primary model
        from sklearn.ensemble import RandomForestClassifier

        # Class weight to favor '1' (Buy) to increase recall
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            class_weight={0: 1, 1: 5},  # Bias towards buying
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X, y)
        return model

    def create_meta_dataset(
        self, X: pd.DataFrame, y_true: pd.Series, primary_model: Any
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Create dataset for Meta-Model.

        Filter X to only rows where Primary Model said "Buy" (1).
        New Label: 1 if y_true was 1 (True Positive), 0 if y_true was 0 (False Positive).
        """
        print("\nmagick Generating Meta-Labels...")

        # Get primary predictions
        y_pred = primary_model.predict(X)

        # Filter: We only care when Primary says BUY
        mask = y_pred == 1

        if mask.sum() == 0:
            raise ValueError("Primary model never predicts Buy! Cannot train Meta-Model.")

        # Meta Features: Subset of X that helps filter false positives
        # (Volatility, Volume, Spread, Regime features)
        # For simplicity, we use ALL features for now, but in production, we select specific ones
        X_meta = X[mask].copy()

        # Meta Labels
        # If Primary=1 and True=1 -> Meta=1 (Keep trade)
        # If Primary=1 and True=0 -> Meta=0 (Filter trade)
        y_meta = y_true[mask].copy()

        print(f"Primary Buys: {mask.sum()}")
        print(f"True Positives: {y_meta.sum()}")
        print(f"False Positives: {(y_meta == 0).sum()}")

        return X_meta, y_meta

    def train_meta_model(self, X_meta: pd.DataFrame, y_meta: pd.Series) -> Any:
        """Train Meta-Model (Optimized for Precision)."""
        print("\n🧠 Training Meta-Model (High Precision)...")

        if XGB_AVAILABLE:
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                eval_metric="logloss",
                use_label_encoder=False,
                random_state=42,
            )
        else:
            from sklearn.ensemble import GradientBoostingClassifier

            model = GradientBoostingClassifier(random_state=42)

        model.fit(X_meta, y_meta)
        return model

    def run(self, pair: str):
        # 1. Load & Process
        df = self.load_data(pair)
        df = self.preprocessor.preprocess(df)
        features = self.engineer.engineer_features(df)

        # Clean features (NaN/Inf)
        features = features.replace([np.inf, -np.inf], np.nan)
        features = features.fillna(0)  # Simple fill for meta-model demo

        labels = self.labeler.create_labels(df)

        # Align
        mask = labels.notna()
        X = features[mask]
        y = labels[mask]

        # Split (Time-series split)
        train_size = int(len(X) * 0.7)
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

        # 2. Train Primary Model
        primary_model = self.train_primary_model(X_train, y_train)

        # Evaluate Primary on Test
        y_prim_test = primary_model.predict(X_test)
        print("\nPrimary Model Test Metrics:")
        print(f"Precision: {precision_score(y_test, y_prim_test):.2f}")
        print(f"Recall:    {recall_score(y_test, y_prim_test):.2f}")

        # 3. Create Meta-Dataset (on Train data)
        # Ideally, we should use cross-val predictions on train data to avoid overfitting
        # But for simplicity in this script, we use the trained model (biased but functional for demo)
        X_meta_train, y_meta_train = self.create_meta_dataset(X_train, y_train, primary_model)

        # 4. Train Meta-Model
        meta_model = self.train_meta_model(X_meta_train, y_meta_train)

        # 5. Evaluate Combined System on Test
        print("\n🔍 Evaluating Combined System...")

        # Step 1: Primary Filter
        primary_signals = primary_model.predict(X_test)

        # Step 2: Meta Filter (only on positive primary signals)
        final_signals = np.zeros_like(primary_signals)

        mask_test = primary_signals == 1
        if mask_test.any():
            meta_preds = meta_model.predict(X_test[mask_test])
            final_signals[mask_test] = meta_preds

        print("Final System Test Metrics:")
        print(f"Precision: {precision_score(y_test, final_signals):.2f}")
        print(f"Recall:    {recall_score(y_test, final_signals):.2f}")
        print(f"F1 Score:  {f1_score(y_test, final_signals):.2f}")

        # Save models
        pair_clean = pair.replace("/", "_")
        with open(self.models_dir / f"{pair_clean}_primary.pkl", "wb") as f:
            pickle.dump(primary_model, f)
        with open(self.models_dir / f"{pair_clean}_meta.pkl", "wb") as f:
            pickle.dump(meta_model, f)

        print(f"\nModels saved to {self.models_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="BTC/USDT")
    args = parser.parse_args()

    trainer = MetaModelTrainer()
    trainer.run(args.pair)
