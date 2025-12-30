# 🚀 Stoic Citadel - Hybrid MFT Trading System

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/github/actions/workflow/status/kandibobe/mft-algotrade-bot/ci.yml?branch=main)
![Architecture](https://img.shields.io/badge/architecture-hybrid-purple)

**The Bridge Between Swing Trading and Mid-Frequency Execution**

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [Roadmap](#-roadmap) • [Docs](docs/)

</div>

## 📋 Overview

Stoic Citadel is an advanced algorithmic trading system that fuses **Machine Learning** with **Mid-Frequency Trading (MFT)** concepts.

Unlike traditional bots that rely solely on lagging indicators, Stoic Citadel implements a **Hybrid Architecture**:
1.  **Macro View:** ML models (XGBoost/LightGBM) analyze 5m/1h candles to determine the trend and regime.
2.  **Micro View:** (In Progress) A real-time Websocket Aggregator monitors spread and orderbook pressure for optimal entry execution.

### 🎯 Key Features

-   **🤖 Regime-Adaptive ML**: Dynamically switches strategies based on Volatility (Hurst Exponent) and Market Phase.
-   **🛡️ Institutional Risk Management**: Volatility-adjusted position sizing, correlation de-risking, and circuit breakers.
-   **🗄️ Persistence Layer**: Unified SQLAlchemy-based database abstraction supporting PostgreSQL and SQLite.
-   **📊 MFT Monitoring**: Real-time Prometheus metrics for orderbook imbalance, spreads, and execution latency.
-   **🔬 Advanced Pipeline**: Feature engineering, time-series cross-validation, and Optuna hyperparameter optimization.
-   **🐳 Production Native**: Fully dockerized with Prometheus/Grafana monitoring and ELK-compatible logging.

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Macro Layer (Freqtrade)"
        A[Market Data (OHLCV)] --> B[Feature Engineering]
        B --> C[ML Inference]
        C --> D[Strategy Decision]
    end

    subgraph "Micro Layer (AsyncIO)"
        E[Websocket Stream] --> F[Data Aggregator]
        F --> G[Real-Time Metrics]
        G --> H[Execution Gate]
    end

    D --> H
    H --> I[Exchange Execution]
```

## 🗺️ Roadmap to Version 6.0

We are currently transitioning from a pure swing bot to a true MFT system.

-   [x] **Phase 1: Foundation (Done)** - Robust ML pipeline, Risk Mixins, Unified Config, and Structured Logging.
-   [x] **Phase 2: Hybrid Connector (Done)** - Connecting Websocket Aggregator to Strategy logic for real-time safety.
-   [x] **Phase 3: Smart Execution (Done)** - Implementing chase-limit orders and async order executor.
-   [x] **Phase 4: Latency Optimization (Done)** - Moving critical paths to async execution and optimizing technical indicators.

See full roadmap in [reports/mft_transformation_roadmap.md](reports/mft_transformation_roadmap.md).

## 🚀 Quick Start

### Prerequisites
-   Python 3.10+
-   Docker & Docker Compose

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/kandibobe/mft-algotrade-bot.git
cd mft-algotrade-bot

# 2. Install dependencies
make install

# 3. Configure
cp .env.example .env
# Edit .env with your keys
```

### Usage

```bash
# Run Backtest
python manage.py backtest

# Run Hyperopt
python manage.py optimize

# Start Production (Docker)
docker-compose up -d
```

## 📚 Documentation

-   **[📂 Project Structure](docs/project_structure.md)** - Where everything lives.
-   **[🩺 Quality Review](reports/code_quality_review.md)** - Current system health.
-   **[🧹 Technical Debt](reports/technical_debt_report.md)** - What we are fixing.
-   **[ML Guide](docs/ADVANCED_PIPELINE_GUIDE.md)** - How the brain works.

## ⚠️ Risk Disclaimer

This software is for educational purposes. **Trading cryptocurrency involves significant risk.** The authors are not responsible for any financial losses incurred.
