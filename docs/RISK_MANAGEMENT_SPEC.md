# Stoic Citadel Risk Management Specification

## 1. Executive Summary
This document defines the comprehensive risk management framework for the Stoic Citadel MFT bot. The system is designed to prevent catastrophic loss (Ruin) while maximizing geometric growth (Kelly) across varying market regimes.

## 2. Risk Hierarchy
The framework operates on three strict levels. Lower levels cannot override higher levels.

1.  **System Level (Circuit Breaker)**: "Can we trade at all?"
2.  **Portfolio Level (Correlation & Allocation)**: "Can we add more risk?"
3.  **Trade Level (Liquidation & Sizing)**: "Is this specific trade safe?"

## 3. Core Components & Rules

### A. Liquidation Guard
**Objective**: Prevent exchange liquidation before stop-loss.
**Rule**: `StopLoss` must be reached before `LiquidationPrice` with a 20% safety buffer.
**Formula**: `|Entry - StopLoss| < |Entry - LiqPrice| * 0.8`
**Action**: If violated, reject trade or reduce leverage.

### B. Correlation Guard
**Objective**: Prevent concentrated exposure to a single risk factor.
**Rule**: Maximum portfolio correlation coefficient `0.7`.
**Action**: Reject new long positions if average correlation of existing portfolio > 0.7.

### C. Volatility Circuit Breaker
**Objective**: Halt trading during extreme volatility events.
**Rule**: Stop trading if:
-   Daily Drawdown > 5%
-   Total Drawdown > 20%
-   Volatility (ATR%) > 8% (Adaptive)

### D. Regime-Adaptive Sizing
**Objective**: Adjust risk based on market capability.

| Regime | Condition | Position Size | Leverage | Stop Loss |
| :--- | :--- | :--- | :--- | :--- |
| **Trending** | Hurst > 0.6 | 100% | 1x-3x | Standard (2x ATR) |
| **Ranging** | Hurst < 0.4 | 80% | 1x | Tight (1.5x ATR) |
| **High Vol** | Vol Rank > 80% | 50% | 1x (No Lev) | Wide (3x ATR) |
| **Noise** | 0.45 < Hurst < 0.55 | 0% | 0x | N/A |

## 4. Implementation Details

### Configuration (`unified_config.py`)
```yaml
risk:
  max_position_pct: 0.10       # Max 10% per trade
  max_portfolio_risk: 0.02     # Max 2% risk per trade
  max_drawdown_pct: 0.20       # 20% hard stop
  liquidation_buffer: 0.20     # 20% distance buffer
  max_correlation: 0.70        # Max correlation
```

### Integration Logic (`StoicRiskMixin`)
The `StoicRiskMixin` acts as a middleware between Freqtrade and the custom `RiskManager`.
1.  **Pre-Trade**: Calls `RiskManager.evaluate_trade()` before every entry.
2.  **Sizing**: Overrides `custom_stake_amount` to apply regime scaling and portfolio limits.
3.  **Monitoring**: Syncs wallet/trade state to `RiskManager` on every iteration.

## 5. Mathematical Justification

### Liquidation Buffer
Given `L` (Leverage) and `MMR` (Maintenance Margin Rate ~0.5%), liquidation occurs at roughly `Entry * (1 - 1/L)`.
For `L=3`, Liq is at -33%.
If Stop Loss is at -5%, Safety = `33% / 5% = 6.6x`. **Safe**.
If `L=10`, Liq is at -10%. Stop Loss at -5%. Safety = `10% / 5% = 2x`. **Marginal**.
If `L=20`, Liq is at -5%. Stop Loss at -5%. **Instant Liquidation Risk**.

### Correlation Impact
Variance of a portfolio `Vp = w^2 * sum(sigma^2) + sum(rho * w_i * w_j * sigma_i * sigma_j)`.
If `rho (correlation)` goes from 0 to 1, portfolio variance increases linearly with N.
Limiting `rho < 0.7` ensures diversification benefits remain active.

## 6. Future Improvements
-   **HRP Integration**: Use Hierarchical Risk Parity for automated rebalancing of weights (currently static).
-   **Options Hedging**: Buying deep OTM puts when Regime = High Volatility.
