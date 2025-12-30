"""
Stoic Citadel - MFT Hybrid System Demo
======================================

This demo showcases the new MFT capabilities:
1. Real-time spread monitoring via Hybrid Connector.
2. Smart Order execution (Chase Limit).
3. Async non-blocking operations.
"""

import asyncio
import logging
import time
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.websocket.aggregator import AggregatedTicker
from src.order_manager.smart_order import ChaseLimitOrder
from src.order_manager.smart_order_executor import SmartOrderExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MFT-Demo")

async def run_demo():
    print("\n🚀 Starting Stoic Citadel MFT Hybrid Demo")
    print("=========================================\n")

    # 1. Initialize Executor
    executor = SmartOrderExecutor()
    await executor.start()

    # 2. Create a Chase Limit Order
    # We want to buy BTC at 50,000, but we'll chase the best bid
    order = ChaseLimitOrder(
        symbol="BTC/USDT",
        quantity=0.1,
        price=49500.0, # Initial low price
        max_chase_price=50100.0 # Never buy above this
    )
    
    print(f"📦 Created ChaseLimitOrder: Symbol={order.symbol}, Initial Price={order.price}, Max Chase={order.max_chase_price}")
    
    order_id = await executor.submit_order(order)
    print(f"✅ Order submitted to executor. ID: {order_id}\n")

    # 3. Simulate Ticker Updates (Market Moving)
    print("📉 Simulating Market Movement...")
    
    market_steps = [
        {"bid": 49600.0, "ask": 49700.0}, # Spread 100
        {"bid": 49800.0, "ask": 49850.0}, # Price rising, spread tightening
        {"bid": 50000.0, "ask": 50020.0}, # Approaching limit
        {"bid": 50200.0, "ask": 50300.0}, # Exceeding max_chase_price
    ]

    for i, step in enumerate(market_steps):
        await asyncio.sleep(1.5)
        
        # Calculate spread
        spread = step['ask'] - step['bid']
        spread_pct = (spread / step['bid']) * 100
        
        ticker = AggregatedTicker(
            symbol="BTC/USDT",
            best_bid=step['bid'],
            best_bid_exchange="binance",
            best_ask=step['ask'],
            best_ask_exchange="binance",
            spread=spread,
            spread_pct=spread_pct,
            exchanges={},
            vwap=step['bid'],
            total_volume_24h=1000.0,
            timestamp=time.time()
        )
        
        print(f"🔔 Ticker Update {i+1}: Bid={ticker.best_bid}, Ask={ticker.best_ask}, Spread={ticker.spread_pct:.2f}%")
        
        # Propagate to executor (internal mechanism)
        await executor._process_ticker_update(ticker)
        
        print(f"   👉 Current Order Price: {order.price}")
        if order.price == order.max_chase_price:
            print("   ⚠️  Price capped at Max Chase Price!")

    # 4. Cleanup
    print("\n🏁 Demo completed successfully.")
    await executor.stop()

if __name__ == "__main__":
    asyncio.run(run_demo())
