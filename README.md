<div align="center">

```
   _____ _             _     _ _     _       _
  / ____| |           (_)   | (_)   | |     | |
 | (___ | |_ ___ _   _ _  __| |_  __| | __ _| |_
  \___ \| __/ _ \ | | | |/ _` | |/ _` |/ _` | __|
  ____) | ||  __/ |_| | | (_| | | (_| | (_| | |_
 |_____/ \__\___|\__,_|_|\__,_|_|\__,_|\__,_|\__|
```

**An open-source framework for building, testing, and deploying institutional-grade crypto trading strategies.**

---

<p align="center">
  <a href="https://github.com/kandibobe/mft-algotrade-bot/actions/workflows/ci.yml">
    <img src="https://github.com/kandibobe/mft-algotrade-bot/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://github.com/kandibobe/mft-algotrade-bot/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </a>
  <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: Black">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Tests-Passing-brightgreen" alt="Tests Passing">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Coverage-90%25+-brightgreen" alt="Code Coverage">
  </a>
</p>

</div>

---

### **Why Stoic Citadel?**

Stoic Citadel is not just another trading bot. It's a comprehensive framework built on a philosophy of robustness and data-driven decisions. Here’s how it compares to standard trading bots:

| Feature Area | Standard Bots | 🛡️ Stoic Citadel |
| :--- | :--- | :--- |
| **🧠 Intelligence** | Simple RSI/MACD logic | Meta-learning ensembles, triple-barrier labeling |
| **🛡️ Risk Management** | Basic stop-loss | Hierarchical Risk Parity, Circuit Breakers |
| **⚡ Performance** | Blocking, high-latency | Asynchronous, low-latency execution core |

---

### **Visual Showcase**

<details>
<summary><strong>Click to see the system in action (placeholder images)</strong></summary>

| Grafana Dashboard | Telegram Bot | Backtest Results |
| :---: | :---: | :---: |
| ![Grafana Placeholder](https://via.placeholder.com/400x250.png?text=Grafana+Dashboard) | ![Telegram Placeholder](https://via.placeholder.com/400x250.png?text=Telegram+Bot+GIF) | ![Backtest Placeholder](https://via.placeholder.com/400x250.png?text=Equity+Curve) |
| Monitor real-time performance and system health. | Control and monitor the bot from anywhere. | Analyze strategy performance with detailed backtests. |

</details>

---

### **Quick Start**

Getting started is as easy as 1-2-3. For detailed instructions, see the [**full documentation**](https://kandibobe.github.io/mft-algotrade-bot/).

| 1️⃣ Clone the Repository | 2️⃣ Configure Your Bot | 3️⃣ Launch with Docker |
| :--- | :--- | :--- |
| `git clone https://github.com/kandibobe/mft-algotrade-bot.git` <br> `cd mft-algotrade-bot` | Create `user_data/config.json` and add your API keys. | `docker-compose up -d` |

<details>
<summary><strong>Click for detailed configuration instructions</strong></summary>

1.  Copy `user_data/config.json.example` to `user_data/config.json`.
2.  Edit the file to include your exchange API keys (`key`, `secret`).
3.  Set your Telegram API credentials (`token`, `chat_id`).
4.  Choose your desired strategy.

</details>

---

### **Repository Map**

```
├── .github/        # GitHub Actions workflows and templates
├── docs/           # The source for the documentation website
├── src/            # Core source code
│   ├── ml/         # Machine learning pipeline
│   ├── risk/       # Risk management and safety
│   └── strategies/ # Strategy logic and connectors
├── tests/          # Unit, integration, and e2e tests
└── user_data/      # Your data: strategies, configs, logs, models
```

---

### **Community & Contributing**

This project is built and maintained by the community. We welcome all contributions!

-   **Found a bug?** [Open a bug report](https://github.com/kandibobe/mft-algotrade-bot/issues/new?template=bug_report.md).
-   **Have a feature idea?** [Suggest a new feature](https://github.com/kandibobe/mft-algotrade-bot/issues/new?template=feature_request.md).
-   **Want to contribute?** Read our [**Contributing Guide**](CONTRIBUTING.md).

### **Sponsor This Project**

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-%E2%9D%A4-%23db61a2.svg)](https://github.com/sponsors/kandibobe)

If you find Stoic Citadel valuable, please consider supporting its development to help us continue to build and improve it.
