# Hybrid MFT Architecture

Stoic Citadel is built on a hybrid architecture that combines the high-level strategic capabilities of Freqtrade with a low-latency, asynchronous micro-execution layer.

## Architectural Overview

The system is divided into two primary layers:

1.  **Macro Layer (Strategy/Sync):** Powered by Python and Freqtrade. This layer handles data processing, technical analysis, and machine learning signal generation. It operates in a synchronous, vectorized manner.
2.  **Micro Layer (Execution/Async):** Built with Python's `asyncio`. This layer handles real-time data aggregation via WebSockets and executes orders with high precision using the `SmartOrderExecutor`.

## Component Interaction

The interaction between these layers is strictly managed by the `HybridConnector`.

```mermaid
graph TD
    subgraph Macro Layer (Sync)
        Strategy[Freqtrade Strategy]
        ML[ML Pipeline]
        Strategy --> ML
    end

    subgraph Bridge
        Connector[HybridConnector]
    end

    subgraph Micro Layer (Async)
        Aggregator[Aggregator]
        RiskManager[Risk Manager]
        Executor[SmartOrderExecutor]
        Exchange[Exchange WS/API]
        
        Aggregator --> RiskManager
        RiskManager --> Executor
        Executor --> Exchange
    end

    ML -. Signals .-> Connector
    Connector --> Aggregator
    Aggregator -. Real-time Data .-> Connector
    Connector --> Strategy
```

## Key Components

### 1. HybridConnector
The `HybridConnector` acts as the bridge. It translates Freqtrade-compatible signals into micro-layer execution tasks and provides the macro layer with real-time micro-data (e.g., orderbook depth, recent trades).

### 2. Aggregator (`src/websocket/aggregator.py`)
A non-blocking WebSocket client that aggregates multiple data streams from various exchanges into a unified internal format.

### 3. SmartOrderExecutor (`src/order_manager/smart_order_executor.py`)
Responsible for executing orders using sophisticated algorithms like `ChaseLimit`, ensuring minimal slippage and high fill rates.

### 4. Risk Manager (`src/risk/risk_manager.py`)
A mandatory gatekeeper for every transaction. It enforces circuit breakers, position sizing limits, and overall portfolio exposure.

## Why this Architecture?

- **Precision:** Standard Freqtrade execution is often too slow for MFT. Our micro-layer handles execution in milliseconds.
- **Safety:** The multi-layered risk management system ensures that even if a strategy fails, the capital is protected.
- **Scalability:** The decoupled nature allows for independent scaling and upgrading of the strategy or execution logic.
