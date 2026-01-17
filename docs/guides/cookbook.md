# Cookbook

This section provides a collection of ready-to-use recipes for common tasks in Stoic Citadel.

---

### Recipe: Running a Vectorized Backtest

This is the fastest way to get a performance overview of a strategy.

```bash
# Activate your environment first
# .venv/Scripts/activate

# Run the backtest script
python scripts/analysis/run_improved_backtest.py --strategy StoicEnsembleStrategyV6 --timerange 20230101-20240101
```

---

### Recipe: Launching a Full System Test

This simulates a live environment using a mock exchange, testing the full hybrid system from signal to execution.

```bash
# Ensure Docker is running
docker-compose -f deploy/docker-compose.test.yml up -d

# Execute the full system verification script
python scripts/verify_full_system.py
```

---

### Recipe: Retraining the Production ML Model

This workflow retrains, validates, and registers a new version of the primary ML model.

```bash
# This script uses the latest data to retrain the model defined in the config
python scripts/ml/retrain_production_model.py

# Optional: Manually trigger Walk-Forward Optimization for the new model
python src/ops/wfo_automation.py --model_version_id <new_version_id>
```

---

### Recipe: Visualizing Feature Importance

Understand which data features are most influential for your model's predictions.

```bash
python scripts/analysis/analyze_feature_importance.py --strategy StoicEnsembleStrategyV6
```

The script will generate and save SHAP summary plots to the `user_data/plot/` directory.

---

*Have a recipe to share? Please [contribute](https://github.com/kandibobe/mft-algotrade-bot/blob/main/CONTRIBUTING.md)!*
