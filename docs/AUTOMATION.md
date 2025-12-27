# 🤖 Automation & Nightly Optimization Guide

Stoic Citadel includes a robust automation suite to keep your trading strategy fresh and profitable.

## The Nightly Optimization Cycle

The core of our automation is the "Nightly Optimization" routine, which performs:
1.  **Deep Hyperopt**: Runs Freqtrade's hyperparameter optimization for 500+ epochs.
2.  **Model Retraining**: Retrains ML models (Random Forest/XGBoost) on the latest data.
3.  **Validation**: Compares new configurations against the baseline.

### How to Run

Use the unified management CLI:

```bash
# Run a full nightly cycle (Hyperopt + ML Training)
python manage.py optimize --epochs 500 --trials 100
```

### Scheduling (Cron)

To run this automatically every night at 2 AM:

```bash
0 2 * * * cd /path/to/mft-algotrade-bot && /path/to/venv/bin/python manage.py optimize >> user_data/logs/nightly.log 2>&1
```

## Continuous Learning (Auto-Retrain)

For a lighter-weight update cycle (just retraining ML models without full hyperopt), use the legacy `auto_retrain.py` script or the `train` command:

```bash
# Train models for specific pairs
python manage.py train --pairs BTC/USDT ETH/USDT --optimize
```

## Monitoring

Check the generated reports in `user_data/hyperopt_results/`:
- `nightly_report_YYYYMMDD.md`: Summary of the optimization run.

Monitor system health:
```bash
python scripts/smoke_test.py
```
