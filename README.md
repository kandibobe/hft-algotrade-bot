<div align="center">

```
   _____ _             _     _ _     _       _
  / ____| |           (_)   | (_)   | |     | |
 | (___ | |_ ___ _   _ _  __| |_  __| | __ _| |_
  \___ \| __/ _ \ | | | |/ _` | |/ _` |/ _` | __|
  ____) | ||  __/ |_| | | (_| | | (_| | (_| | |_
 |_____/ \__\___|\__,_|_|\__,_|_|\__,_|\__,_|\__|
```

**Institutional-Grade Mid-Frequency Trading (MFT) System**

---

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Hybrid%20Async-blueviolet" alt="Architecture">
  <img src="https://img.shields.io/badge/Risk-Institutional-red" alt="Risk Management">
  <img src="https://img.shields.io/badge/Execution-MFT-blue" alt="Execution">
</p>

</div>

---

### **Overview**

Stoic Citadel is a next-generation crypto trading framework designed to bridge the gap between traditional Algo-Trading bots (like Freqtrade) and HFT/MFT institutional systems.

It utilizes a **Hybrid Architecture**:
1.  **Macro Layer (Strategy):** Freqtrade-based synchronous logic for trend analysis and regime detection.
2.  **Micro Layer (Execution):** AsyncIO-based WebSocket Aggregator and Smart Order Executor for low-latency market interaction.

### **Key Features**

| Feature | Description |
| :--- | :--- |
| **🚀 Hybrid Connector** | Seamless bridge between Strategy loop and real-time Websocket data. |
| **🧠 Feature Store** | Production-grade Feature Store (Feast/Redis) for online/offline consistency. |
| **🛡️ Unified Risk Engine** | Centralized `RiskManager` implementing Circuit Breakers, Drawdown protection, and HRP sizing. |
| **⚡ Smart Execution** | `ChaseLimit`, `Pegged`, and `Iceberg` orders to minimize slippage and impact. |
| **📊 Regime Detection** | Dynamic strategy adaptation based on Hurst Exponent and Volatility Z-Score. |

---

### **Architecture**

```mermaid
graph TD
    A[Market Data (WS)] -->|Async| B(Data Aggregator)
    B -->|Real-time Ticker| C{Smart Executor}
    B -->|Metrics| D[Hybrid Connector]
    
    E[Freqtrade Strategy] -->|Signal| D
    D -->|Order Request| C
    
    C -->|Order Placement| F[Exchange API]
    
    subgraph Risk Gate
    G[Risk Manager] -->|Check| C
    G -->|Check| D
    end
```

---

### **Getting Started**

#### 1. Configuration
The system uses a **Unified Configuration** system (`src/config/manager.py`).
Copy `.env.example` to `.env` and set your credentials:

```bash
cp .env.example .env
# Edit .env with your API Keys and Settings
```

#### 2. Deployment
Run with Docker Compose (includes Redis for Feature Store):

```bash
docker-compose up -d --build
```

#### 3. Development
Install dependencies:

```bash
pip install -r requirements.txt
pre-commit install
```

---

### **Project Structure**

*   `src/strategies/`: Trading strategies and Hybrid Connector.
*   `src/order_manager/`: Async Smart Order Execution logic.
*   `src/websocket/`: Real-time data aggregation.
*   `src/risk/`: Centralized risk management.
*   `src/ml/`: Machine Learning pipeline and Feature Store.
*   `src/config/`: Unified configuration system.

---

### **License**

MIT License. See [LICENSE](LICENSE) for details.
