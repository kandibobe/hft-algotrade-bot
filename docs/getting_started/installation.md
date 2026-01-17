# Installation Guide

This guide provides step-by-step instructions for setting up the Stoic Citadel hybrid MFT system.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **Docker & Docker Compose**
- **Git**
- **Freqtrade** (optional, for standalone strategy testing)

## 1. Clone the Repository

```bash
git clone https://github.com/kandibobe/mft-algotrade-bot.git
cd mft-algotrade-bot
```

## 2. Environment Setup

### Using Virtual Environment (Recommended for Development)

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```
2.  **Activate the virtual environment:**
    - Windows: `.venv\Scripts\activate`
    - Linux/macOS: `source .venv/bin/activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Using Docker (Recommended for Production/Deployment)

The project includes a `docker-compose.yml` for quick setup of all services including Redis, PostgreSQL, and the trading bot.

```bash
docker-compose up -d
```

## 3. Configuration

1.  **Copy the template environment file:**
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Fill in your API keys, exchange secrets, and database credentials.
3.  **Validate configuration:**
    ```bash
    python scripts/maintenance/validate_config.py
    ```

## 4. Initialize Database and ML System

Run the initialization scripts to set up the necessary database schemas and ML registry.

```bash
python scripts/setup/init_db.py
python scripts/setup/init_ml_system.py
```

## Next Steps

Once installed, proceed to the [Quick Start](quick_start.md) guide to run your first backtest.
