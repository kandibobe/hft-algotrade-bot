import asyncio
import random
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mock objects for dependencies that would exist in the main application
class MockWsClient:
    def __init__(self):
        self.received = []
        self.connected = True

    async def recv(self):
        if not self.connected:
            raise ConnectionError("WebSocket is closed")
        # Simulate receiving a trade message
        await asyncio.sleep(0.01) # Simulate network latency
        return f'{{"e":"trade","s":"BTCUSDT","p":"{69000 + random.uniform(-50, 50):.2f}"}}'

    async def close(self):
        self.connected = False
        logging.info("Mock WebSocket client closed.")

class MockSmartOrderExecutor:
    async def execute_order(self, order_details):
        logging.info(f"Chaos Test: Mock execute_order called with {order_details}")
        # Simulate execution latency or failure
        if random.random() < 0.1: # 10% chance of execution failure
            logging.error("Chaos Test: Simulated order execution failure!")
            return {"status": "FAILED"}
        await asyncio.sleep(random.uniform(0.05, 0.2))
        logging.info("Chaos Test: Simulated order execution successful.")
        return {"status": "FILLED"}

# The component we are testing
async def data_processing_loop(ws_client, executor):
    """A simplified version of a loop that processes data and might execute trades."""
    while ws_client.connected:
        try:
            message = await ws_client.recv()
            logging.info(f"Received message: {message[:80]}...")
            
            # Simulate a trading decision
            if random.random() < 0.2: # 20% chance to trigger a trade
                logging.warning("Chaos Test: Trade condition met, attempting to execute.")
                await executor.execute_order({"symbol": "BTCUSDT", "action": "BUY"})

        except ConnectionError as e:
            logging.error(f"Connection lost: {e}. Attempting to reconnect...")
            await asyncio.sleep(1) # Cooldown before reconnect
            ws_client.connected = True # Simulate successful reconnection
        except Exception as e:
            logging.critical(f"An unexpected error occurred in the data loop: {e}")
            break

# --- Chaos Engineering Scenarios ---

async def scenario_network_latency(ws_client):
    """Chaos Scenario: Introduce random network latency."""
    logging.warning("CHAOS: Injecting high network latency...")
    original_recv = ws_client.recv
    async def delayed_recv():
        await asyncio.sleep(random.uniform(0.5, 2.0))
        return await original_recv()
    ws_client.recv = delayed_recv
    await asyncio.sleep(10) # Run with latency for 10 seconds
    ws_client.recv = original_recv # Restore normal behavior
    logging.warning("CHAOS: Network latency injection finished.")

async def scenario_connection_drop(ws_client):
    """Chaos Scenario: Simulate a sudden WebSocket connection drop."""
    logging.warning("CHAOS: Forcing connection drop...")
    ws_client.connected = False
    await asyncio.sleep(5) # Let the system try to reconnect
    logging.warning("CHAOS: Connection drop simulation finished.")

async def scenario_api_failures(executor):
    """Chaos Scenario: Simulate intermittent order execution failures."""
    logging.warning("CHAOS: Injecting API execution failures...")
    original_execute = executor.execute_order
    async def faulty_execute(order):
        if random.random() < 0.5: # 50% chance of failure during chaos
            logging.error("CHAOS: Simulated API failure!")
            return {"status": "REJECTED"}
        return await original_execute(order)
    executor.execute_order = faulty_execute
    await asyncio.sleep(15)
    executor.execute_order = original_execute
    logging.warning("CHAOS: API failure injection finished.")


async def main():
    mock_ws = MockWsClient()
    mock_executor = MockSmartOrderExecutor()

    logging.info("Starting Chaos Test for the Asynchronous Execution Layer.")
    
    # Run the main data processing loop in the background
    main_task = asyncio.create_task(data_processing_loop(mock_ws, mock_executor))

    # Sequentially run chaos scenarios
    await asyncio.sleep(5) # Let it run normally for a bit
    await scenario_network_latency(mock_ws)
    await asyncio.sleep(5)
    await scenario_connection_drop(mock_ws)
    await asyncio.sleep(5)
    await scenario_api_failures(mock_executor)
    
    # Clean up
    main_task.cancel()
    await mock_ws.close()
    
    logging.info("Chaos Test finished. Review logs for system behavior under stress.")


if __name__ == "__main__":
    asyncio.run(main())
