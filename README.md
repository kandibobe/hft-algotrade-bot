# 🏛 Stoic Citadel: Hybrid MFT Trading System

[![Build Status](https://github.com/kandibobe/mft-algotrade-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/kandibobe/mft-algotrade-bot/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-green)](CHANGELOG.md)

**Stoic Citadel** is a high-performance, hybrid Mid-Frequency Trading (MFT) system designed for cryptocurrency markets. It combines the strategic depth of [Freqtrade](https://www.freqtrade.io/) with a custom asynchronous execution layer for low-latency order management and advanced ML-driven decision making.

---

## 🌟 Key Features

*   **Hybrid Architecture**: Synchronous macro-strategy layer + Asynchronous micro-execution layer.
*   **Smart Order Execution**: Custom `ChaseLimit` logic to minimize slippage and maximize fill rates.
*   **ML-Powered Decision Gate**: Production-ready model registry and Feast feature store integration.
*   **Institutional Risk Management**: Real-time correlation analysis, HRP position sizing, and multi-level circuit breakers.
*   **Enterprise Monitoring**: Comprehensive ELK stack logging and Prometheus/Grafana dashboards.

---

## 🏗 Architecture Overview

The system is split into two primary boundaries to ensure both strategic flexibility and execution speed:

1.  **Macro Layer (Strategy)**: Handles signal generation, pair selection, and high-level portfolio management.
2.  **Micro Layer (Execution)**: Validates signals against real-time order books and manages the lifecycle of orders with sub-millisecond precision.

For more details, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🚦 Quick Start

### 1. Prerequisites
*   Python 3.10+
*   Docker & Docker Compose
*   Redis (for feature caching)

### 2. Installation
```bash
git clone https://github.com/kandibobe/mft-algotrade-bot.git
cd mft-algotrade-bot
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Configuration
Copy the template and fill in your API credentials:
```bash
cp config.json.example config.json
```
*Note: `config.json` is automatically ignored by Git for your security.*

---

## 📊 Performance & Monitoring

### Dashboard Showcase
> **[TODO: Вставьте сюда скриншот вашего Grafana дашборда]**
> *Пример: `![Grafana Dashboard](docs/img/grafana_sample.png)`*

### Latest Backtest Results (v2.0.0)
| Metric | Value |
| :--- | :--- |
| **ROI** | [TODO: %] |
| **Max Drawdown** | [TODO: %] |
| **Sharpe Ratio** | [TODO: x.xx] |
| **Win Rate** | [TODO: %] |

---

## 🔒 Security First

*   **Zero Leakage Policy**: Proprietary strategies and production configs are strictly excluded via `.gitignore`.
*   **Sanitized History**: This repository is maintained with a clean history suitable for public collaboration.
*   **Local-Only Mode**: All sensitive data stays on your machine.

---

## 📜 Documentation Index

*   [Strategic Development Guide](docs/STRATEGY_DEVELOPMENT_GUIDE.md)
*   [ML Pipeline & Training](docs/ML_TRAINING_PIPELINE.md)
*   [Order Management Specification](docs/ORDER_MANAGEMENT.md)
*   [Risk Management Specs](docs/RISK_MANAGEMENT_SPEC.md)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) and our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

Developed with 🏛 **Stoic Citadel Team**.
