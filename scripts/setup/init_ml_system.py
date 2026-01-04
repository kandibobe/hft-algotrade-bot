import os

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# Stoic Citadel ML Imports
from src.ml.feature_store import create_feature_store
from src.ml.training.model_registry import ModelRegistry
from src.utils.logger import log as logger


def init_ml_system():
    """
    Initialize the ML infrastructure by setting up the Feature Store
    and training a dummy production model.
    """
    logger.info("🛠 Initializing Stoic Citadel ML System...")

    # 1. Ensure directories exist
    os.makedirs("user_data/models", exist_ok=True)
    os.makedirs("user_data/models/registry", exist_ok=True)

    # 2. Initialize Feature Store
    logger.info("📦 Setting up Feature Store...")
    try:
        # Try creating with Feast first
        fs = create_feature_store(use_mock=False)
        fs.initialize()
        fs.register_features()
        logger.info("✅ Feast Feature Store initialized.")
    except Exception as e:
        logger.warning(f"⚠️ Feast initialization failed ({e}). Falling back to MockFeatureStore.")
        fs = create_feature_store(use_mock=True)
        fs.initialize()
        fs.register_features()
        logger.info("✅ Mock Feature Store initialized.")

    # 3. Generate Mock Training Data (10 days of 5m data)
    logger.info("📊 Generating mock training data for BTC/USDT...")
    # In a real scenario, we'd use dp.get_pair_dataframe or freqtrade download-data
    # Here we create synthetic data for the dummy model
    n_samples = 2880  # 10 days * 24 hours * 12 (5m intervals)
    X = np.random.rand(n_samples, 20)  # 20 dummy features
    y = np.random.randint(0, 2, n_samples)  # Binary target (0 or 1)

    feature_names = [f"feature_{i}" for i in range(20)]
    X_df = pd.DataFrame(X, columns=feature_names)

    # 4. Train Dummy XGBClassifier
    logger.info("🤖 Training dummy XGBClassifier...")
    model = XGBClassifier(
        n_estimators=10,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric="logloss",
    )
    model.fit(X_df, y)

    # 5. Save Model and Register in Registry
    model_path = "user_data/models/production_model.pkl"
    joblib.dump(model, model_path)
    logger.info(f"💾 Dummy model saved to {model_path}")

    # Register in ModelRegistry
    registry = ModelRegistry()
    registry.register_model(
        model_name="stoic_ensemble_v6",
        model_path=model_path,
        feature_names=feature_names,
        metrics={"accuracy": 0.5},  # Dummy metric
        version="1.0.0",
    )

    # Also save as a direct file for simple loaders
    joblib.dump(model, "user_data/models/production_model.pkl")

    logger.info("🚀 ML System Initialization Complete!")
    logger.info("\nRun Instruction:")
    logger.info("python scripts/init_ml_system.py")


if __name__ == "__main__":
    init_ml_system()
