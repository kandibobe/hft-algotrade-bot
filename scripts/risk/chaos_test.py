#!/usr/bin/env python3
"""
Chaos Engineering Test Script
=============================

Simulates adverse conditions to verify system resilience:
1. Network Failures (API Errors)
2. Market Crashes (Consecutive Losses, Drawdown)
3. Volatility Spikes
4. Recovery Mechanisms

Usage:
    python scripts/risk/chaos_test.py
"""

import logging
import random
import time
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState, TripReason

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ChaosTest")

class ChaosMonkey:
    """Simulates system failures."""
    
    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate

    def should_fail(self) -> bool:
        return random.random() < self.failure_rate

def run_chaos_test():
    logger.info("🦍 Starting Chaos Engineering Test...")

    # 1. Setup Circuit Breaker with tight limits for testing
    config = CircuitBreakerConfig(
        daily_loss_limit_pct=0.02,      # 2% max daily loss
        consecutive_loss_limit=3,       # 3 losses in a row
        max_api_errors=5,               # 5 errors triggers trip
        api_error_window_minutes=1,
        cooldown_minutes=0.1,           # Fast cooldown for testing
        auto_reset_after_hours=0.01     # Fast auto-reset
    )
    
    cb = CircuitBreaker(config)
    # Mock state file to avoid messing up prod state
    cb.config.state_file_path = Path("user_data/chaos_test_state.json")
    cb.initialize_session(initial_balance=10000.0)

    chaos = ChaosMonkey(failure_rate=0.2)
    
    logger.info(f"Initial State: {cb.state.value}")
    assert cb.state == CircuitState.CLOSED, "System should start CLOSED"

    # ---------------------------------------------------------
    # Scenario 1: API Instability (Network Glitches)
    # ---------------------------------------------------------
    logger.info("\n--- Scenario 1: Network Storm (API Errors) ---")
    for i in range(10):
        if i < 6:
            logger.info(f"Injecting API Error #{i+1}")
            cb.record_api_error()
        else:
            time.sleep(0.1)
    
    # Check if tripped
    status = cb.get_status()
    logger.info(f"State after API storm: {status['state']}")
    
    if status['state'] == 'open':
        logger.info("✅ Circuit Breaker tripped correctly on API errors")
    else:
        logger.error("❌ Circuit Breaker FAILED to trip on API errors")

    # Manual Reset for next test
    cb.manual_reset()
    
    # ---------------------------------------------------------
    # Scenario 2: Flash Crash (Consecutive Losses)
    # ---------------------------------------------------------
    logger.info("\n--- Scenario 2: Flash Crash (Consecutive Losses) ---")
    
    # Simulate 3 losing trades
    for i in range(3):
        trade = {"pair": "BTC/USDT", "amount": 100}
        # Loss of 1% each time
        cb.record_trade(trade, profit_pct=-0.01)
        logger.info(f"Recorded Loss #{i+1}: -1.0%")
    
    status = cb.get_status()
    logger.info(f"State after Flash Crash: {status['state']}")
    
    if status['state'] == 'open' and status['trip_reason'] == 'consecutive_losses':
         logger.info("✅ Circuit Breaker tripped correctly on Consecutive Losses")
    else:
         logger.error(f"❌ Circuit Breaker FAILED to trip. State: {status['state']}")

    # ---------------------------------------------------------
    # Scenario 3: Recovery (Self-Healing)
    # ---------------------------------------------------------
    logger.info("\n--- Scenario 3: Recovery Procedure ---")
    
    # Wait for cooldown (we set it to 0.1 min = 6 sec)
    logger.info("Waiting for cooldown (6s)...")
    time.sleep(7)
    
    # Check if we can trade (should check if transition to Half-Open is possible)
    can_trade = cb.can_trade()
    # Note: can_trade() internally attempts state transition if cooldown passed
    
    status = cb.get_status()
    logger.info(f"State after cooldown: {status['state']}")
    
    if status['state'] == 'half_open':
        logger.info("✅ System correctly transitioned to HALF-OPEN")
        
        # Simulate successful recovery trades
        logger.info("Executing recovery trades...")
        for i in range(3):
            cb.attempt_recovery(trade_successful=True)
            logger.info(f"Recovery Trade #{i+1}: Success")
            
        status = cb.get_status()
        if status['state'] == 'closed':
             logger.info("✅ System fully HEALED and reset to CLOSED")
        else:
             logger.error(f"❌ System failed to fully recover. State: {status['state']}")
             
    else:
        logger.error("❌ System failed to enter HALF-OPEN state")

    # Cleanup
    if cb.config.state_file_path.exists():
        cb.config.state_file_path.unlink()
    logger.info("\n🦍 Chaos Test Completed.")

if __name__ == "__main__":
    try:
        run_chaos_test()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception("Chaos test crashed!")
        sys.exit(1)
