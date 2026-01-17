
import cProfile
import pstats
import asyncio
import time
from src.websocket.aggregator import DataAggregator
from src.websocket.data_stream import TickerData, TradeData, OrderbookData, Exchange

async def main():
    aggregator = DataAggregator(aggregation_interval=0.01)
    aggregator.add_exchange(Exchange.BINANCE, ["BTC/USDT"], ["ticker", "trade", "orderbook"])
    
    async def data_generator():
        for i in range(10000):
            ts = time.time()
            ticker = TickerData(symbol="BTC/USDT", bid=50000 + i, ask=50001 + i, last=50000.5 + i, exchange="binance", volume_24h=1000+i, timestamp=ts, change_24h=0.0)
            await aggregator._process_ticker(ticker)
            
            trade = TradeData(symbol="BTC/USDT", trade_id=str(i), side="buy", price=50000.5 + i, quantity=1, timestamp=ts, exchange="binance")
            await aggregator._process_trade(trade)

            orderbook = OrderbookData(symbol="BTC/USDT", bids=[[50000+i, 1]], asks=[[50001+i, 1]], timestamp=ts, exchange="binance")
            await aggregator._process_orderbook(orderbook)

    profiler = cProfile.Profile()
    profiler.enable()

    await data_generator()

    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()

if __name__ == "__main__":
    asyncio.run(main())
