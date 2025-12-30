#!/bin/bash
# Nightly Optimization Script
# Run via cron: 0 0 * * * /path/to/run_nightly.sh

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Set paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/user_data/logs/nightly_opt_$(date +%Y%m%d).log"

cd "$PROJECT_ROOT"

# Ensure log directory exists
mkdir -p "$PROJECT_ROOT/user_data/logs"

echo "Starting Nightly Optimization at $(date)" >> "$LOG_FILE"

# Activate virtualenv (adjust path if needed)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run optimization
# This runs the NightlyOptimizer which trains models and optimizes hyperparameters
python manage.py optimize --epochs 100 --trials 50 >> "$LOG_FILE" 2>&1

echo "Finished Nightly Optimization at $(date)" >> "$LOG_FILE"
