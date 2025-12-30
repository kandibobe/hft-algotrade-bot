"""
Smart Order Executor
====================

Manages and executes Smart Orders using asynchronous event loop.
Provides the bridge between high-level smart order logic and low-level exchange calls.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.order_manager.order_types import Order, OrderStatus, OrderType
from src.order_manager.smart_order import SmartOrder, ChaseLimitOrder
from src.websocket.aggregator import DataAggregator, AggregatedTicker

logger = logging.getLogger(__name__)

class SmartOrderExecutor:
    """
    Asynchronous executor for Smart Orders.
    
    Features:
    - Non-blocking order management
    - Real-time price adjustments based on ticker updates
    - Automatic retry and error handling
    """
    
    def __init__(self, aggregator: Optional[DataAggregator] = None):
        self.aggregator = aggregator
        self._active_orders: Dict[str, SmartOrder] = {}
        self._order_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the executor service."""
        self._running = True
        logger.info("Smart Order Executor started")
        
        # If aggregator is provided, subscribe to ticker updates
        if self.aggregator:
            @self.aggregator.on_aggregated_ticker
            async def handle_ticker(ticker: AggregatedTicker):
                await self._process_ticker_update(ticker)

    async def stop(self):
        """Stop the executor and cancel all active order tasks."""
        self._running = False
        async with self._lock:
            for task in self._order_tasks.values():
                task.cancel()
            self._order_tasks.clear()
            self._active_orders.clear()
        logger.info("Smart Order Executor stopped")

    async def submit_order(self, order: SmartOrder) -> str:
        """
        Submit a new smart order for execution.
        """
        async with self._lock:
            order.update_status(OrderStatus.SUBMITTED)
            self._active_orders[order.order_id] = order
            
            # Start a background task to monitor/manage this specific order
            task = asyncio.create_task(self._manage_order(order))
            self._order_tasks[order.order_id] = task
            
            logger.info(f"Submitted Smart Order {order.order_id} ({order.symbol})")
            return order.order_id

    async def cancel_order(self, order_id: str):
        """Cancel an active smart order."""
        async with self._lock:
            if order_id in self._active_orders:
                order = self._active_orders[order_id]
                order.update_status(OrderStatus.CANCELLED)
                
                if order_id in self._order_tasks:
                    self._order_tasks[order_id].cancel()
                    del self._order_tasks[order_id]
                
                del self._active_orders[order_id]
                logger.info(f"Cancelled Smart Order {order_id}")

    async def _manage_order(self, order: SmartOrder):
        """
        Internal loop to manage an individual order's lifecycle.
        """
        try:
            while order.is_active:
                # 1. Check for timeout
                if order.check_timeout():
                    break
                
                # 2. In a real implementation, we would check the fill status from the exchange
                # For this implementation, we assume external updates via update_fill
                
                await asyncio.sleep(1.0) # Check every second
                
        except asyncio.CancelledError:
            logger.debug(f"Order management task for {order.order_id} cancelled")
        except Exception as e:
            logger.error(f"Error managing order {order.order_id}: {e}")
            order.update_status(OrderStatus.FAILED, error=str(e))
        finally:
            async with self._lock:
                if order.order_id in self._active_orders:
                    del self._active_orders[order.order_id]
                if order.order_id in self._order_tasks:
                    del self._order_tasks[order.order_id]

    async def _process_ticker_update(self, ticker: AggregatedTicker):
        """
        Handle ticker updates and propagate them to relevant smart orders.
        """
        async with self._lock:
            # Create a list of orders to avoid dictionary mutation during iteration
            orders_to_update = [
                order for order in self._active_orders.values() 
                if order.symbol == ticker.symbol and order.is_active
            ]
            
        for order in orders_to_update:
            try:
                # Convert AggregatedTicker to simple dict for SmartOrder
                ticker_dict = {
                    'best_bid': ticker.best_bid,
                    'best_ask': ticker.best_ask,
                    'spread_pct': ticker.spread_pct
                }
                
                old_price = getattr(order, 'price', None)
                order.on_ticker_update(ticker_dict)
                new_price = getattr(order, 'price', None)
                
                if old_price != new_price:
                    # Trigger exchange order replacement if needed
                    await self._replace_exchange_order(order)
                    
            except Exception as e:
                logger.error(f"Error processing ticker update for order {order.order_id}: {e}")

    async def _replace_exchange_order(self, order: SmartOrder):
        """
        Placeholder for exchange API call to replace/modify an open order.
        """
        logger.debug(f"Exchange call: Replacing order {order.order_id} with new price {order.price}")
        # In real implementation:
        # await self.exchange.replace_order(order.exchange_order_id, order.price, ...)
        pass

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get the current status of an order."""
        if order_id in self._active_orders:
            return self._active_orders[order_id].status
        return None
