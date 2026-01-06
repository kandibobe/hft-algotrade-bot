#!/bin/bash
# Auto-Retrain Script for MLOps (Host Version)
# Usage: ./scripts/maintenance/auto_retrain.sh

echo "🚀 Starting Daily Retraining Pipeline..."

# 1. Download latest data
echo "📥 Downloading fresh market data..."
docker-compose -f deploy/docker-compose.yml run --rm freqtrade download-data --config user_data/config/config_production.json --days 2 -t 5m 1h

# 2. Train Model
echo "🧠 Training Model..."
docker-compose -f deploy/docker-compose.yml run --rm freqtrade freqai-train --config user_data/config/config_production.json --strategy StoicEnsembleStrategyV6 --days 30

echo "✅ Retraining complete."
