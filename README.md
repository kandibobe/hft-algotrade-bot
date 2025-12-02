# 🏛️ STOIC CITADEL - HFT Algorithmic Trading Bot

**Professional trading infrastructure powered by Freqtrade**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Freqtrade 2024.11](https://img.shields.io/badge/freqtrade-2024.11-green.svg)](https://www.freqtrade.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start-windows)
- [Strategies](#-available-strategies)
- [Backtesting](#-backtesting)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)

---

## ✨ Features

### Trading Infrastructure
- 🤖 **Freqtrade 2024.11** - Professional algorithmic trading engine
- 📊 **FreqUI Dashboard** - Real-time monitoring and control
- 🐳 **Docker-based** - One-command deployment
- 💾 **PostgreSQL** - Advanced analytics database
- 🔍 **Portainer** - Container management

### Strategies Included
1. **SimpleTestStrategy** - Basic RSI strategy for testing
2. **StoicStrategyV1** - Market regime-aware trend following
3. **StoicEnsembleStrategy** - Multi-strategy ensemble

### Research & Development
- 🔬 **Jupyter Lab** - Interactive strategy development
- 📈 **Backtesting** - Walk-forward validation
- 🎯 **HyperOpt** - Parameter optimization
- 📊 **Rich Analytics** - pandas, numpy, scikit-learn

---

## 🚀 Quick Start (Windows)

### Prerequisites
- ✅ Docker Desktop installed and running
- ✅ Git for Windows
- ✅ PowerShell 5.0+

### Installation

```powershell
# Clone repository
git clone https://github.com/kandibobe/hft-algotrade-bot.git
cd hft-algotrade-bot

# Start bot (dry-run mode, no real money)
docker-compose up -d freqtrade frequi

# Check status
docker-compose ps
```

**Dashboard:** http://localhost:3000  
**Login:** `stoic_admin` | **Password:** `StoicGuard2024`

### Using Helper Script

```powershell
# Start bot
.\citadel.ps1 start

# Download data
.\citadel.ps1 download

# Run backtest
.\citadel.ps1 backtest

# Show all commands
.\citadel.ps1 help
```

---

## 🎯 Available Strategies

### SimpleTestStrategy
**Best for:** Testing infrastructure, learning basics

```yaml
Logic: Buy when RSI < 30, Sell when RSI > 70
ROI: 5% / 3% / 1%
Stoploss: -5%
Timeframe: 5m
```

### StoicStrategyV1
**Best for:** Production trading, bull markets

```yaml
Logic: Market regime filter + RSI oversold + trend confirmation
ROI: 6% / 4% / 2% / 1%
Stoploss: -5%
Timeframe: 5m
Special: Requires BTC/USDT 1d data for regime detection
```

### StoicEnsembleStrategy
**Best for:** Advanced users, risk diversification

```yaml
Logic: Combines multiple sub-strategies with voting
ROI: Dynamic based on sub-strategies
Stoploss: -5%
Timeframe: 5m
```

---

## 🧪 Backtesting

### Quick Test

```powershell
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy `
  --timerange 20241001-20241202
```

### Download Historical Data

```powershell
# 90 days, 5-minute candles
docker-compose run --rm freqtrade download-data `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance `
  --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
  --timeframe 5m `
  --days 90
```

### Advanced Backtesting

```powershell
# With daily breakdown
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy StoicStrategyV1 `
  --timerange 20240601- `
  --breakdown day

# View results
docker-compose run --rm freqtrade backtesting-show
```

---

## 📁 Project Structure

```
hft-algotrade-bot/
├── user_data/
│   ├── strategies/           # Trading strategies
│   │   ├── SimpleTestStrategy.py
│   │   ├── StoicStrategyV1.py
│   │   └── StoicEnsembleStrategy.py
│   ├── data/binance/         # Market data
│   ├── logs/                 # Bot logs
│   ├── config/
│   │   └── config.json       # Main configuration
│   └── tradesv3.sqlite       # Trade database
├── research/                 # Jupyter notebooks
├── scripts/                  # Helper scripts
├── docker/                   # Docker configurations
├── docker-compose.yml        # Main orchestration file
├── citadel.ps1              # Windows helper script
├── START_WINDOWS.md         # Detailed Windows guide
└── README.md                # This file
```

---

## 📚 Documentation

- **[START_WINDOWS.md](START_WINDOWS.md)** - Complete Windows setup guide
- **[QUICKSTART.md](QUICKSTART.md)** - 3-minute quick start
- **[Freqtrade Docs](https://www.freqtrade.io/en/stable/)** - Official documentation

---

## 🔧 Configuration

### Main Config: `user_data/config/config.json`

```json
{
  "dry_run": true,              // ⚠️ Set false for real trading
  "dry_run_wallet": 10000,      // Virtual wallet in dry-run
  "stake_amount": "unlimited",  // Position sizing
  "max_open_trades": 3,         // Maximum concurrent trades
  "exchange": {
    "name": "binance",
    "key": "",                   // Your API key
    "secret": ""                 // Your API secret
  }
}
```

---

## 🛠️ Common Commands

```powershell
# Start bot
docker-compose up -d freqtrade frequi

# Stop bot
docker-compose down

# View logs
docker-compose logs -f freqtrade

# List strategies
docker-compose run --rm freqtrade list-strategies `
  --config /freqtrade/user_data/config/config.json

# Check status
docker-compose ps
```

---

## ⚠️ Risk Disclaimer

**IMPORTANT:** This software is for educational purposes. Algorithmic trading carries substantial risk of financial loss. The authors are not responsible for any losses incurred.

- ✅ Always test strategies in dry-run mode first
- ✅ Start with small amounts
- ✅ Understand the risks
- ✅ Never invest more than you can afford to lose

---

## 📈 Performance Monitoring

### Real-time Dashboard
- **URL:** http://localhost:3000
- **Features:** Live trades, performance metrics, profit/loss tracking

### Logs
```powershell
# Real-time logs
docker-compose logs -f freqtrade

# Save to file
docker-compose logs freqtrade > logs.txt

# View log file
notepad user_data/logs/freqtrade.log
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🔗 Links

- **GitHub:** https://github.com/kandibobe/hft-algotrade-bot
- **Freqtrade:** https://www.freqtrade.io/
- **Documentation:** See `START_WINDOWS.md` for detailed guide

---

**🏛️ Stoic Citadel** - Where reason rules, not emotion.

*Built with ❤️ by algorithmic traders, for algorithmic traders*
