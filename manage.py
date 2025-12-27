#!/usr/bin/env python3
"""
Stoic Citadel Management CLI
============================

Unified entry point for all operations.

Usage:
    python manage.py train --pairs BTC/USDT ETH/USDT
    python manage.py backtest
    python manage.py optimize
"""

import argparse
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("manage")

def setup_path():
    """Ensure src is in python path."""
    root = Path(__file__).parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

setup_path()

def train_command(args):
    """Execute model training."""
    from src.ml.pipeline import MLTrainingPipeline
    
    logger.info(f"Starting training for {args.pairs}")
    pipeline = MLTrainingPipeline(
        quick_mode=args.quick
    )
    pipeline.run(
        pairs=args.pairs,
        timeframe=args.timeframe,
        optimize=args.optimize,
        n_trials=args.trials
    )

def optimize_command(args):
    """Execute nightly optimization."""
    from src.ops.optimization import NightlyOptimizer
    
    optimizer = NightlyOptimizer()
    optimizer.execute_nightly_cycle(
        strategy=args.strategy,
        pairs=args.pairs,
        epochs=args.epochs,
        ml_trials=args.trials
    )

def backtest_command(args):
    """Execute backtest."""
    import subprocess
    
    cmd = [
        "freqtrade", "backtesting",
        "--strategy", args.strategy,
        "--timeframe", args.timeframe,
        "--config", "config/config_backtest.json"
    ]
    
    if args.timerange:
        cmd.extend(["--timerange", args.timerange])
        
    if args.pairs:
        cmd.extend(["--pairs"] + args.pairs)
        
    logger.info(f"Running backtest: {' '.join(cmd)}")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Stoic Citadel Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # TRAIN
    train_parser = subparsers.add_parser("train", help="Train ML models")
    train_parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT"], help="Pairs to train")
    train_parser.add_argument("--timeframe", default="5m", help="Timeframe")
    train_parser.add_argument("--quick", action="store_true", help="Quick mode (less data)")
    train_parser.add_argument("--optimize", action="store_true", help="Run hyperparameter optimization")
    train_parser.add_argument("--trials", type=int, default=50, help="Number of optimization trials")
    
    # OPTIMIZE
    opt_parser = subparsers.add_parser("optimize", help="Run nightly optimization")
    opt_parser.add_argument("--strategy", default="StoicEnsembleStrategyV4", help="Strategy class name")
    opt_parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT"], help="Pairs to optimize")
    opt_parser.add_argument("--epochs", type=int, default=100, help="Hyperopt epochs")
    opt_parser.add_argument("--trials", type=int, default=50, help="ML optimization trials")

    # BACKTEST
    bt_parser = subparsers.add_parser("backtest", help="Run backtest")
    bt_parser.add_argument("--strategy", default="StoicEnsembleStrategyV4", help="Strategy class name")
    bt_parser.add_argument("--timeframe", default="5m", help="Timeframe")
    bt_parser.add_argument("--timerange", help="Timerange (e.g. 20240101-)")
    bt_parser.add_argument("--pairs", nargs="+", help="Override pairs")
    
    args = parser.parse_args()
    
    if args.command == "train":
        train_command(args)
    elif args.command == "optimize":
        optimize_command(args)
    elif args.command == "backtest":
        backtest_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
