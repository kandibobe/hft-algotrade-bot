"""
ML Training Pipeline Module
===========================

Core logic for training ML models.
Moved from scripts/train_models.py for better organization.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from src.ml.training.feature_engineering import FeatureEngineer
from src.ml.training.labeling import TripleBarrierLabeler, TripleBarrierConfig
from src.ml.training.model_trainer import ModelTrainer, TrainingConfig
from src.ml.training.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

class MLTrainingPipeline:
    """Full ML Training Pipeline."""

    def __init__(
        self,
        data_dir: str = None,
        models_dir: str = None,
        quick_mode: bool = False
    ):
        from src.config.manager import config
        try:
            cfg = config()
            exchange_name = cfg.exchange.name
        except Exception:
            logger.warning("Config not initialized, defaulting to binance")
            exchange_name = "binance"

        self.data_dir = Path(data_dir or f"user_data/data/{exchange_name}")
        self.models_dir = Path(models_dir or "user_data/models")
        self.quick_mode = quick_mode

        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.labeler = TripleBarrierLabeler(config=TripleBarrierConfig())
        # Use registry inside models_dir
        self.registry = ModelRegistry(registry_dir=str(self.models_dir / "registry"))

    def load_data(self, pairs: List[str], timeframe: str = "5m") -> Dict[str, pd.DataFrame]:
        """Load data from feather or JSON files."""
        logger.info("="*70)
        logger.info("📥 LOADING DATA")
        logger.info("="*70)

        data = {}

        for pair in pairs:
            pair_filename = pair.replace('/', '_')
            feather_filename = f"{pair_filename}-{timeframe}.feather"
            json_filename = f"{pair_filename}-{timeframe}.json"
            
            feather_path = self.data_dir / feather_filename
            json_path = self.data_dir / json_filename

            if feather_path.exists():
                filepath = feather_path
                filetype = 'feather'
            elif json_path.exists():
                filepath = json_path
                filetype = 'json'
            else:
                logger.warning(f"⚠️  {pair}: File not found - {feather_filename} or {json_filename}")
                continue

            logger.info(f"📊 Loading {pair} from {filetype}...")

            if filetype == 'feather':
                df = pd.read_feather(filepath)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                elif 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                else:
                    df.set_index(df.columns[0], inplace=True)
                    df.index = pd.to_datetime(df.index, unit='ms')
            else:
                with open(filepath, 'r') as f:
                    json_data = json.load(f)
                df = pd.DataFrame(
                    json_data,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)

            logger.info(f"  ✅ Loaded {len(df):,} candles")
            logger.info(f"  📅 Range: {df.index[0]} to {df.index[-1]}")

            # Data Validation
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if df[required_cols].isnull().any().any():
                nan_count = df[required_cols].isnull().sum().sum()
                logger.warning(f"  ⚠️  {pair}: Found {nan_count} NaNs in OHLCV data. Dropping...")
                df = df.dropna(subset=required_cols)
                
            if len(df) < 100:
                logger.warning(f"  ⚠️  {pair}: Insufficient data ({len(df)} rows). Skipping.")
                continue

            if self.quick_mode:
                df = df.tail(1000)
                logger.info(f"  ⚡ Quick mode: Using last 1000 candles")

            data[pair] = df

        if not data:
            raise ValueError(f"No data found in {self.data_dir}")

        logger.info("="*70)
        return data

    def prepare_features_and_labels(
        self,
        df: pd.DataFrame,
        pair: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and labels."""
        logger.info(f"\n🔧 Feature Engineering for {pair}...")

        # FIX: Use prepare_data to generate features WITHOUT scaling/selection
        # This allows us to scale later on split data to avoid leakage
        features = self.feature_engineer.prepare_data(df)
        logger.info(f"  ✅ Generated {len(features.columns)} features (unscaled)")

        is_valid, issues = self.feature_engineer.validate_features(
            features,
            fix_issues=True,
            raise_on_error=False
        )

        if issues['nan_columns']:
            logger.info(f"  ⚠️  Fixed NaN in {len(issues['nan_columns'])} columns")
        if issues['inf_columns']:
            logger.info(f"  ⚠️  Fixed Inf in {len(issues['inf_columns'])} columns")

        logger.info(f"\n🏷️  Labeling for {pair}...")
        labels = self.labeler.label(df)

        logger.info(f"  ✅ Generated {len(labels)} labels")
        
        label_counts = labels.value_counts()
        for label_val, count in label_counts.items():
            label_name = {1: 'LONG', 0: 'NEUTRAL', -1: 'SHORT'}.get(label_val, 'UNKNOWN')
            pct = (count / len(labels)) * 100
            logger.info(f"     {label_name:8s}: {count:6,} ({pct:5.1f}%)")

        common_index = features.index.intersection(labels.index)
        X = features.loc[common_index]
        y = labels.loc[common_index]

        nan_mask = y.isna()
        if nan_mask.any():
            logger.info(f"  ⚠️  Removing {nan_mask.sum()} rows with NaN labels")
            X = X[~nan_mask]
            y = y[~nan_mask]

        logger.info(f"\n  ✅ Final dataset: {len(X):,} samples, {len(X.columns)} features")
        return X, y

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        pair: str,
        optimize: bool = False,
        n_trials: int = 100
    ) -> Tuple[Any, Dict[str, float]]:
        """Train model."""
        logger.info(f"\n🤖 Training Model for {pair}...")

        # 3-way time-series split (60% Train, 20% Validation, 20% Test)
        # Train: Learn patterns
        # Val: Optimize hyperparameters (avoid overfitting to train)
        # Test: Final unbiased evaluation (avoid overfitting to val)
        train_end = int(len(X) * 0.6)
        val_end = int(len(X) * 0.8)
        
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]

        logger.info(f"  📊 Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

        # FIX: Fit scaler and selector on TRAIN data only to prevent leakage
        logger.info("  ⚖️  Fitting scaler and selecting features on TRAIN set...")
        X_train = self.feature_engineer.fit_scaler_and_selector(X_train)
        
        # Apply transformation to Val and Test
        logger.info("  ⚖️  Transforming Val and Test sets...")
        X_val = self.feature_engineer.transform_scaler_and_selector(X_val)
        X_test = self.feature_engineer.transform_scaler_and_selector(X_test)

        config = TrainingConfig(
            model_type="random_forest",
            optimize_hyperparams=optimize,
            n_trials=n_trials if optimize else 10,
            use_time_series_split=True,
            n_splits=3 if self.quick_mode else 5,
            save_model=True,
            models_dir=str(self.models_dir)
        )

        try:
            from imblearn.over_sampling import SMOTE
            class_counts = y_train.value_counts()
            if len(class_counts) > 1:
                min_class_ratio = class_counts.min() / class_counts.max()
                if min_class_ratio < 0.3:
                    logger.info(f"  ⚖️  Applying SMOTE for class balancing (ratio: {min_class_ratio:.3f})")
                    smote = SMOTE(random_state=42)
                    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
                    logger.info(f"  📊 After SMOTE: {len(X_train_resampled)} samples (was {len(X_train)})")
                    X_train = X_train_resampled
                    y_train = y_train_resampled
        except ImportError:
            logger.warning("  ⚠️  imblearn not installed, skipping SMOTE")
        
        trainer = ModelTrainer(config)
        # Train on Train set, Validate on Validation set
        model, val_metrics = trainer.train(X_train, y_train, X_val, y_val)

        # Calculate final metrics on Test set (Unbiased)
        logger.info(f"\n  🧪 Evaluating on Test Set...")
        
        # Ensure features match (if feature selection was applied)
        if hasattr(model, "feature_names_in_"):
            # Filter X_test to match training features
            cols = model.feature_names_in_
            X_test = X_test[cols]
            
        y_pred = model.predict(X_test)
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, average="weighted", zero_division=0),
            "recall": recall_score(y_test, y_pred, average="weighted", zero_division=0),
            "f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        }

        logger.info(f"\n  ✅ Model trained successfully!")
        logger.info(f"  📊 Test Metrics (Held-out):")
        for metric_name, value in metrics.items():
            logger.info(f"     {metric_name:15s}: {value:.4f}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_name = f"{pair.replace('/', '_')}_{timestamp}"
        model_path = self.models_dir / f"{model_name}.pkl"
        
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        self.registry.register_model(
            model_name=pair.replace('/', '_'),
            model_path=str(model_path),
            metrics=metrics,
            training_config={
                'pair': pair,
                'features': X.columns.tolist(),
                'training_date': datetime.now().isoformat(),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
            },
            feature_names=X.columns.tolist(),
            tags=['quick_training' if self.quick_mode else 'full_training']
        )

        logger.info(f"  💾 Model saved: {model_path}")

        scaler_name = f"{model_name}_scaler.joblib"
        scaler_path = self.models_dir / scaler_name
        self.feature_engineer.save_scaler(str(scaler_path))
        logger.info(f"  💾 Scaler saved: {scaler_path}")

        return model, metrics

    def run(
        self,
        pairs: List[str],
        timeframe: str = "5m",
        optimize: bool = False,
        n_trials: int = 100
    ) -> Dict[str, Any]:
        """Run full training pipeline."""
        logger.info("="*70)
        logger.info("🚀 ML MODEL TRAINING PIPELINE")
        logger.info("="*70)
        logger.info(f"\nConfiguration:")
        logger.info(f"  Pairs:      {', '.join(pairs)}")
        logger.info(f"  Timeframe:  {timeframe}")
        logger.info(f"  Optimize:   {optimize}")
        logger.info(f"  Quick mode: {self.quick_mode}")

        data = self.load_data(pairs, timeframe)
        results = {}

        for pair, df in data.items():
            logger.info("\n" + "="*70)
            logger.info(f"🎯 TRAINING: {pair}")
            logger.info("="*70)

            try:
                X, y = self.prepare_features_and_labels(df, pair)
                model, metrics = self.train_model(X, y, pair, optimize, n_trials)
                results[pair] = {'success': True, 'metrics': metrics}
            except Exception as e:
                logger.error(f"\n❌ Error training {pair}: {e}", exc_info=True)
                results[pair] = {'success': False, 'error': str(e)}

        logger.info("\n" + "="*70)
        logger.info("📊 TRAINING SUMMARY")
        logger.info("="*70)

        for pair, result in results.items():
            if result['success']:
                metrics = result['metrics']
                logger.info(f"\n✅ {pair}")
                logger.info(f"   Accuracy:  {metrics.get('accuracy', 0):.4f}")
                logger.info(f"   F1 Score:  {metrics.get('f1', 0):.4f}")
            else:
                logger.info(f"\n❌ {pair}")
                logger.info(f"   Error: {result['error']}")

        logger.info("\n" + "="*70)
        logger.info("✅ TRAINING COMPLETED!")
        logger.info("="*70)
        
        return results
