# 🏗️ MFT Hybrid Architecture

Stoic Citadel uses a dual-layer architecture to balance deep statistical analysis with high-speed execution.

## 1. Architecture Overview

The system is divided into two main loops:

### 🐢 Macro Layer (Strategy Loop)
- **Framework:** Freqtrade (Synchronous)
- **Data:** 5m/1h Candles (OHLCV)
- **Responsibility:** 
    - Trend analysis
    - Regime detection (Hurst, Volatility)
    - ML Inference (XGBoost/LightGBM)
    - Risk management and position sizing
- **Latency:** ~Seconds

### 🐇 Micro Layer (Execution Loop)
- **Framework:** AsyncIO / Websockets
- **Data:** Tick-level, Orderbook snapshots
- **Responsibility:**
    - Real-time spread monitoring
    - Orderbook imbalance analysis
    - Smart order execution (Chase Limit)
    - Emergency flash-crash protection
- **Latency:** < 100ms

## 2. Key Components

### 🌉 Hybrid Connector (`src/strategies/hybrid_connector.py`)
Bridges the two layers. It runs a background thread with an `asyncio` loop to power the websocket aggregator while providing thread-safe metrics to the main strategy.

### 📊 Data Aggregator (`src/websocket/aggregator.py`)
Consolidates real-time streams from multiple exchanges to find the best global bid/ask and detect cross-exchange opportunities.

### 🎯 Smart Order Executor (`src/order_manager/smart_order_executor.py`)
Handles MFT execution logic. Instead of standard limit orders, it uses `ChaseLimitOrder` which automatically adjusts its price to stay at the top of the orderbook, reducing slippage and increasing fill probability.

## 3. Data Flow

1.  **Macro Analysis:** The strategy loop identifies a "Buy" regime and high ML probability.
2.  **Safety Gate:** The `confirm_trade_entry` method queries the `HybridConnector` for real-time spread. If spread > 0.5%, the trade is blocked.
3.  **Smart Execution:** If safe, the `SmartOrderExecutor` is tasked with entering the position using a chasing limit order.
4.  **Real-time Adjustment:** As the orderbook moves, the executor updates the limit price in real-time until filled or timed out.

## 4. Latency Optimizations

- **Numpy Vectorization:** All technical indicators are calculated using optimized numpy arrays.
- **Fast Hashing:** Cache keys for indicators use a lightweight shape+tail hash instead of full object serialization.
- **Async ML Inference:** Model predictions are handled via a non-blocking Redis queue to prevent freezing the main loop.
