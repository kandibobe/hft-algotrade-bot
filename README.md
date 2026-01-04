# MFT Algotrade Bot (Stoic Citadel)

A hybrid Mid-Frequency Trading (MFT) bot combining Freqtrade's robust strategy engine with custom high-performance execution logic.

## 🚀 Features

*   **Hybrid Architecture**: Freqtrade for strategy signals + AsyncIO for execution.
*   **Stoic Ensemble Strategy**: Multi-strategy ensemble with regime detection.
*   **Smart Order Execution**: `ChaseLimit` logic for optimal entry/exit.
*   **Risk Management**: Integrated risk manager with circuit breakers.
*   **Telegram Companion Bot**: Full-featured interactive bot for alerts, portfolio tracking, and market news.

## 🤖 Telegram Companion Bot

The project now includes an advanced interactive Telegram bot (ported from `bot-finance-tg`).

### Features:
- **Price Alerts**: Set alerts like "BTC > 100000" or "ETH +5%".
- **Watchlist**: Track your favorite assets.
- **Market News**: Get the latest crypto news (via CryptoPanic/NewsAPI).
- **Volatility Scanner**: See top gainers and losers.
- **Portfolio Tracking**: Manually track your crypto portfolio.

### Setup:
1.  Ensure `TELEGRAM_BOT_TOKEN` is set in your `.env` file.
2.  (Optional) Add API keys for full functionality:
    *   `NEWS_API_ORG_KEY` (for general news)
    *   `CRYPTO_PANIC_API_KEY` (for crypto news)
    *   `ALPHA_VANTAGE_API_KEY` (for forex/stocks)
    *   `FRED_API_KEY` (for economic data)

### Running the Bot:
You can run the Telegram bot as a standalone process:
```bash
python -m src.telegram_bot.runner
```

## 🛠 Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Copy `.env.example` to `.env` and configure your keys.

## 📈 Usage

Run the main trading bot:
```bash
freqtrade trade --config config.json --strategy StoicEnsembleStrategy
```

Run the Telegram companion bot:
```bash
python -m src.telegram_bot.runner
```

## 📚 Documentation

*   [Telegram Bot Guide](docs/TELEGRAM_BOT.md)
*   [Architecture](docs/ARCHITECTURE.md)
*   [Risk Management](docs/RISK_MANAGEMENT_SPEC.md)
