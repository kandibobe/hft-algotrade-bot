"""
Configuration Package Initialization
====================================

This file exports the primary components from the unified_config module,
making them easily accessible from other parts of the application.

By centralizing the exports here, we can ensure that the entire application
relies on the same robust and validated configuration system.

Usage:
    from src.config import TradingConfig, load_config, config

    # Load the main configuration
    main_config = load_config("config/strategy_config.yaml")

    # Get the global singleton
    cfg = config()

    # Type-hinting with the config model
    def process_data(config: TradingConfig):
        if not config.dry_run:
            print("Executing live trade!")
"""

from .unified_config import TradingConfig, load_config, ConfigWatcher
from .manager import config

__all__ = [
    "TradingConfig",
    "load_config",
    "ConfigWatcher",
    "config",
]
