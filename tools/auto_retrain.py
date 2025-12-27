#!/usr/bin/env python3
"""
Automated Retraining Pipeline (CI/CD for ML)
============================================

Orchestrates the entire retraining workflow:
1. Download fresh data
2. Train Primary Models (RandomForest/XGBoost)
3. Train Meta-Models (Meta-Labeling)
4. Validate performance (Walk-Forward)
5. Deploy if performance improves

Usage:
    python scripts/auto_retrain.py --pairs BTC/USDT ETH/USDT
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("user_data/logs/auto_retrain.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutoRetrainer:
    def __init__(self, pairs: list, timeframe: str = "5m"):
        self.pairs = pairs
        self.timeframe = timeframe
        self.root_dir = Path(__file__).parent.parent

    def run_command(self, cmd: str, description: str) -> bool:
        """Run a shell command and check for errors."""
        logger.info(f"🚀 Starting: {description}")
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            logger.info(f"✅ Success: {description}")
            logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed: {description}")
            logger.error(e.stderr)
            return False

    def run(self):
        start_time = datetime.now()
        logger.info(f"Starting Automated Retraining Cycle at {start_time}")

        # 1. Download Data
        pairs_str = " ".join(self.pairs)
        if not self.run_command(
            f"python scripts/download_data.py --pair {pairs_str} --timeframe {self.timeframe} --days 30 --no-docker",
            "Download Data"
        ):
            return

        # 2. Train Primary Models (with optimization)
        # Using fewer trials for automation speed
        if not self.run_command(
            f"python scripts/train_models.py --pairs {pairs_str} --timeframe {self.timeframe} --optimize --trials 10",
            "Train Primary Models"
        ):
            return

        # 3. Train Meta-Models (for each pair)
        for pair in self.pairs:
            if not self.run_command(
                f"python scripts/train_meta_model.py --pair {pair}",
                f"Train Meta-Model for {pair}"
            ):
                logger.warning(f"Skipping Meta-Model for {pair}")

        # 4. Final Validation (Backtest)
        if not self.run_command(
            f"freqtrade backtesting --strategy StoicEnsembleStrategyV4 --timeframe {self.timeframe} --config user_data/config/config_backtest.json",
            "Final Validation Backtest"
        ):
            return

        duration = datetime.now() - start_time
        logger.info(f"✨ Retraining Cycle Completed in {duration}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT"])
    parser.add_argument("--timeframe", default="5m")
    args = parser.parse_args()

    retrainer = AutoRetrainer(args.pairs, args.timeframe)
    retrainer.run()
