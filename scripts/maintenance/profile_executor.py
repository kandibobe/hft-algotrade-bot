
import cProfile
import pstats
import asyncio
from src.order_manager.smart_order_executor import SmartOrderExecutor
from src.order_manager.smart_order import ChaseLimitOrder
from src.websocket.aggregator import AggregatedTicker
from unittest.mock import MagicMock, AsyncMock

async def main():
    # Mock exchange
    exchange = MagicMock()
    exchange.create_order = AsyncMock(return_value={"id": "123"})
    exchange.fetch_order = AsyncMock(return_value={"status": "closed"})
    exchange.fetch_ticker = AsyncMock(return_value={"ask": 50000.0, "bid": 49999.0})
    
    # Mock aggregator
    aggregator = MagicMock()
    aggregator.get_aggregated_ticker.return_value = AggregatedTicker(
        symbol="BTC/USDT",
        best_bid=49999.0,
        best_ask=50000.0,
        best_bid_exchange="mock",
        best_ask_exchange="mock",
        spread=1.0,
        spread_pct=0.002,
        exchanges={},
        vwap=50000,
        total_volume_24h=1000,
        timestamp=0
    )

    executor = SmartOrderExecutor(aggregator=aggregator, dry_run=True)
    
    order = ChaseLimitOrder(
        symbol="BTC/USDT",
        side="buy",
        quantity=0.01,
        price=50000.0,
        chase_offset=10,
        max_chase_price=50010.0
    )

    profiler = cProfile.Profile()
    profiler.enable()

    await executor.submit_order(order)

    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()

if __name__ == "__main__":
    asyncio.run(main())
