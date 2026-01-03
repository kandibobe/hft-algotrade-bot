# 🗺️ Project Roadmap

This document outlines the development roadmap for Stoic Citadel. Our goal is to be transparent about our priorities and upcoming features.

## Guiding Principles
*   **Stability First:** Core infrastructure must be robust and reliable.
*   **Quant-Driven:** Features should be based on sound quantitative finance principles.
*   **Performance:** Latency and throughput are critical metrics.
*   **Modularity:** New components should be decoupled and independently testable.

---

## ⛔ **Phase 1-4: Hybrid MFT Core (Completed)**

-   [x] **Foundation:** Robust ML pipeline, Risk Mixins, Unified Config.
-   [x] **Hybrid Connector:** Websocket Aggregator & Strategy Bridge.
-   [x] **Smart Execution:** Async Order Executor & Chase Limit Logic.
-   [x] **Optimization:** Latency reduction and safety checks.
-   [x] **V2.0 Release:** HRP, Meta-Learning, Feature Store.

---

## ✅ **Phase 5: Alpha Generation & Execution (Current Focus)**

### Q1 2026
*   **[Target: In Progress] Alternative Data Integration:**
    *   Integrate sentiment analysis from sources like Twitter/StockTwits.
    *   Add support for on-chain analytics (e.g., Glassnode metrics).
*   **[Target: In Progress] Advanced Order Types:**
    *   Implement Iceberg Orders for reducing market impact.
    *   Develop a "Pegged Order" type that tracks the best bid/ask.
*   **[Target: Planned] Options & Derivatives Data:**
    *   Integrate options chain data (Greeks, Implied Volatility).
    *   Build initial models for volatility arbitrage strategies.

### Q2 2026
*   **[Target: Planned] Cross-Exchange Arbitrage Module:**
    *   Develop a low-latency price comparison engine.
    *   Build a dedicated execution path for statistical arbitrage.
*   **[Target: Planned] GPU-Accelerated Backtesting:**
    *   Refactor the vectorized backtester to use `cuDF` and `Numba`.
    *   Aim for a >10x speedup in Monte Carlo simulations.

---

## ➡️ **Phase 6: Decentralized & AI-Driven (Future)**

### Q3 2026
*   **[Target: Research] DeFi Integration:**
    *   Connectors for interacting with DEXs (e.g., Uniswap v3, dYdX).
    *   Strategies for liquidity provision and yield farming.
*   **[Target: Research] Reinforcement Learning (RL) Agent:**
    *   Develop an RL agent for dynamic parameter optimization.
    *   Use the RL agent to manage position sizing and risk exposure.

### Q4 2026 and Beyond
*   **[Target: Vision] Fully Autonomous Strategy Generation:**
    *   Research AI techniques for discovering new trading strategies.
    *   Build a "strategy sandbox" where AI can safely test new alphas.
*   **[Target: Vision] High-Performance Rust Core:**
    *   Rewrite the most latency-sensitive components (e.g., websocket aggregator, order book) in Rust.

---

## Contribution

We welcome contributions! If you have an idea for a feature, please open a [Feature Request](/.github/ISSUE_TEMPLATE/feature_request.md) to discuss it.
