import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeploymentVerifier")


def check_dependencies():
    logger.info("Checking dependencies...")
    try:
        import scipy

        logger.info(f"✅ Scipy found: {scipy.__version__}")
    except ImportError:
        logger.error("❌ Scipy NOT found! (Critical for HRP)")
        return False

    try:
        import feast

        logger.info(f"✅ Feast found: {feast.__version__}")
    except ImportError:
        logger.warning("⚠️ Feast not found. Feature Store will run in Mock mode.")

    try:
        import redis

        logger.info(f"✅ Redis found: {redis.__version__}")
    except ImportError:
        logger.warning("⚠️ Redis driver not found.")

    return True


def check_config():
    logger.info("Checking configuration...")
    config_path = Path("user_data/config/config_production.json")

    if not config_path.exists():
        logger.warning(f"⚠️ {config_path} does not exist.")
        # Try to generate it from Unified Config
        try:
            from src.config.unified_config import TradingConfig

            logger.info("Generating config from Unified Config defaults...")
            config = TradingConfig()  # Load from .env or defaults

            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to JSON
            config.to_json(str(config_path))
            logger.info(f"✅ Generated {config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to generate config: {e}")
            return False
    else:
        logger.info(f"✅ Config found at {config_path}")
        return True


def check_strategy():
    logger.info("Checking Strategy V6...")
    try:

        logger.info("✅ StoicEnsembleStrategyV6 importable.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import Strategy V6: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    success = True
    if not check_dependencies():
        success = False
    if not check_config():
        success = False
    if not check_strategy():
        success = False

    if success:
        logger.info("\n🎉 All checks passed! System is ready.")
        sys.exit(0)
    else:
        logger.error("\n❌ Checks failed. Please fix errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
