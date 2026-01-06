# Installation

This guide will walk you through the steps to set up the Stoic Citadel trading bot.

## Prerequisites

- Python 3.10+
- Docker
- Git

## Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kandibobe/mft-algotrade-bot.git
    cd mft-algotrade-bot
    ```

2.  **Set up the environment:**
    - **Using Docker (Recommended):**
      ```bash
      docker-compose up -d
      ```
    - **Manual Installation:**
      ```bash
      python -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
      ```

3.  **Configure the bot:**
    - Copy `config.json.example` to `config.json`.
    - Edit `config.json` with your exchange API keys and other settings.

## Next Steps

Once the installation is complete, you can proceed to the **[Quick Start](quick_start.md)** guide.
