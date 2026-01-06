# 🛡️ Stoic Citadel: Hybrid MFT Trading System

[![CI](https://github.com/kandibobe/mft-algotrade-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/kandibobe/mft-algotrade-bot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Stoic Citadel is an institutional-grade, hybrid Mid-Frequency Trading (MFT) system designed for robustness, speed, and intelligence. It combines the strategic depth of Freqtrade with a custom-built, low-latency execution layer based on Python's AsyncIO.

---

## 📖 Documentation

**The complete documentation is available at [our documentation site](https://kandibobe.github.io/mft-algotrade-bot/).**

This site includes:
-   **Getting Started:** Installation and setup guides.
-   **Architecture:** In-depth explanations of the system's design.
-   **Guides:** Tutorials for strategy development, risk management, and more.
-   **API Reference:** Auto-generated documentation for the source code.

---

## 🏛 Core Architecture

The system is decoupled into two primary layers to balance statistical depth with execution speed:

- **Macro Layer (Intelligence):** Handles long-term alpha generation, regime detection, and portfolio optimization. Powered by an ensemble of ML models (XGBoost/LightGBM) and Freqtrade.
- **Micro Layer (Execution):** A high-speed execution loop (<100ms) managing real-time orderbook dynamics, smart limit chasing, and emergency safety guards.

## 🚀 Key Features

- **Advanced ML Pipeline:** Triple barrier labeling, meta-labeling, walk-forward optimization, and SHAP feature selection.
- **Institutional Risk Management:** Hierarchical Risk Parity (HRP), Fractional Kelly Criterion, circuit breakers, and drift analysis.
- **Smart Execution Engine:** ChaseLimit logic, iceberg orders, maker-fee optimization, and self-healing mechanisms.

## 🛠 Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kandibobe/mft-algotrade-bot.git
    cd mft-algotrade-bot
    ```

2.  **Follow the documentation:**
    All setup and usage instructions are now available in the official documentation. Please see the **[Getting Started](https://kandibobe.github.io/mft-algotrade-bot/getting_started/installation/)** guide.

## 🤝 Contributing

Contributions are welcome! Please read our [**Contributing Guide**](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and more.

---
*Stoic Citadel - Built for stability, optimized for speed, driven by data.*
