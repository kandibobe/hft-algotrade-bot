# Telegram Companion Bot for Stoic Citadel

This module is a powerful, interactive Telegram bot integrated into the Stoic Citadel trading system. It allows you to monitor the market, set alerts, and track your portfolio directly from Telegram.

## Features

*   **Real-time Alerts**:
    *   Price Alerts: "BTC > 100000", "ETH < 2000"
    *   Percent Alerts: "BTC +5%", "SOL -10%"
    *   RSI Alerts: "BTC RSI > 70"
*   **Watchlist**:
    *   Add/Remove assets to your personal watchlist.
    *   Get a quick summary of your watchlist prices.
*   **Market Data**:
    *   **Fear & Greed Index**: Visualize market sentiment.
    *   **Volatility**: Top 5 Gainers and Losers (24h).
    *   **Trending**: Trending coins on CoinGecko.
    *   **News**: Latest crypto news from CryptoPanic.
    *   **ETH Gas**: Current gas prices (Safe/Propose/Fast).
*   **Portfolio**:
    *   Manually add assets to track your holdings.
    *   Calculate total portfolio value in USD.
*   **Daily Digest**:
    *   Configurable morning summary of market state (default 07:00 UTC).

## Setup & Configuration

### 1. Environment Variables
Add the following to your `.env` file:

```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id  # Optional, for admin notifications

# Optional (for full functionality)
NEWS_API_ORG_KEY=your_key_here       # For general financial news
CRYPTO_PANIC_API_KEY=your_key_here   # For crypto news
ALPHA_VANTAGE_API_KEY=your_key_here  # For Forex/Stock data
FRED_API_KEY=your_key_here           # For US Economic data (GDP, etc.)
ETHERSCAN_API_KEY=your_key_here      # For Gas prices
GLASSNODE_API_KEY=your_key_here      # For on-chain metrics
```

### 2. Dependencies
Ensure you have installed the requirements:
```bash
pip install -r requirements.txt
```

## Running the Bot

### Standalone Mode
To run the bot as a separate process (recommended for development or if running alongside Freqtrade in Docker):

```bash
python -m src.telegram_bot.runner
```

### Usage
Start a chat with your bot and use the `/start` command.

**Commands:**
*   `/start` - Open main menu
*   `/help` - Show help message
*   `/report` - Market Report (Interactive)
*   `/signal` - Get technical signals
*   `/watchlist` - Show watchlist
*   `/addwatch <symbol>` - Add to watchlist (e.g. `/addwatch BTC`)
*   `/delwatch` - Remove from watchlist
*   `/alerts` - Manage alerts
*   `/addalert` - Interactive alert creation
*   `/settings` - Bot settings (Language, Alerts, etc.)
*   `/portfolio` - Portfolio tracker

**Quick Alert Syntax:**
You can just type:
*   `BTC > 50000`
*   `ETH +5%`
*   `SOL -10%`

## Architecture
The bot uses `python-telegram-bot` (v20+) with asyncio.
*   **Handlers**: Logic for each command (`src/telegram_bot/handlers/`)
*   **Services**: Data fetching and business logic (`src/telegram_bot/services/`)
*   **Database**: SQLite database stored in `user_data/bot_database.db` to persist alerts and watchlists.
*   **Jobs**: Background tasks (`src/telegram_bot/jobs.py`) check alerts every minute.
