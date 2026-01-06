# Backtesting Guide

This repository includes a rigorous, **Event-Driven Backtesting Engine** designed specifically for Machine Learning strategies.

## 🚨 Why Standard Backtesting Fails for ML

Standard backtesting tools (like simple vectorization) often fail for ML because:
1.  **Lookahead Bias:** ML models can accidentally "see" the future if data isn't split strictly chronologically.
2.  **Execution Mismatch:** ML models often predict "Trade Horizon" (e.g., "Will hit TP in 12 bars"), but naive backtesters re-evaluate every bar, leading to huge turnover and fee burn.
3.  **Cost Blindness:** Ignoring spread, slippage, and fees turns losing high-frequency strategies into winners on paper.

## ✅ The Solution: Event-Driven Vectorized Backtester

We have implemented `src/backtesting/vectorized_backtester.py` which enforces:
-   **Strict Causality:** Signals generated at `Close[t]` are executed at `Open[t+1]`.
-   **Trade Lifecycle:** Simulates holding a position until Take Profit, Stop Loss, or Time Limit is hit.
-   **Fee Reality:** Deducts 0.1% fee + 0.05% slippage on *every* trade.

---

## 🛠️ How to Run Backtests

### 1. Simple Backtest (Train/Test Split)

Use this for quick validation of a model idea. It splits data into Train (70%) and Test (30%), trains a model, and backtests on the unseen Test data.

```bash
python scripts/backtest.py --symbol BTC/USDT --timeframe 5m --start 2024-01-01 --end 2024-03-01
```

**Output:**
```
BACKTEST RESULTS (Test Set Only)
Total Return: 5.23%
Final Capital: $10523.00
Trades: 42
Win Rate: 55.00%
Avg Net PnL: $12.45
```

### 2. Walk-Forward Validation (Gold Standard)

Use this for production readiness. It simulates a "rolling" retraining process:
1.  Train on Jan-Mar -> Test on Apr.
2.  Train on Feb-Apr -> Test on May.
3.  ...

This prevents overfitting to specific market regimes.

```bash
python scripts/walk_forward_backtest.py --pair BTC/USDT --timeframe 5m --train-months 3 --test-months 1
```

---

## ⚠️ Important Note on Freqtrade Backtesting

The file `user_data/strategies/StoicEnsembleStrategyV4.py` is designed for **Live Trading** via Freqtrade.

**Do NOT** blindly run `freqtrade backtesting` with this strategy unless you are certain the ML model file loaded was trained on data **older** than your backtest start date. If you train on 2024 data and backtest on 2024, your results will be fake (Lookahead Bias).

**Recommendation:**
1.  Use `scripts/walk_forward_backtest.py` to validate the ML logic.
2.  Use Freqtrade backtesting only for logic *around* the ML (like trailing stops, ROI) using a "frozen" model trained on past data.
