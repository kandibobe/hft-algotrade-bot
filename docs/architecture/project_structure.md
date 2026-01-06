# 📂 Project Structure & Architecture

**Stoic Citadel - Version 5.2.0**

This document defines the canonical folder structure for the project. All new code must adhere to this schema.

## 1. Top-Level Directory
```
mft-algotrade-bot/
├── config/                 # User Configuration (Strategy, Exchange, Dry Run)
├── deploy/                 # Deployment (Docker, Kubernetes, Scripts)
├── docs/                   # Documentation (Guides, Architecture, API)
├── monitoring/             # Observability (Grafana, Prometheus, Alertmanager)
├── reports/                # Generated Reports (Quality, Backtest Results)
├── src/                    # CORE SOURCE CODE (See Section 2)
├── strategies/             # Trading Strategies (Freqtrade Implementations)
├── tests/                  # Test Suite (Unit, Integration, Functional)
├── tools/                  # Utility Scripts (Ops, Maintenance)
├── user_data/              # Runtime Data (Backtest Results, Models, DB)
├── manage.py               # Unified CLI Entry Point
└── Makefile                # Development Automation
```

## 2. Source Code (`src/`)

The core logic is organized by domain in `src/`.

```
src/
├── config/                 # Configuration Management
│   ├── manager.py          # [PLANNED] Unified Config Manager
│   └── ...
├── data/                   # Data Access Layer
│   ├── loader.py           # OHLCV Loading
│   └── downloader.py       # Exchange Downloading
├── ml/                     # Machine Learning Pipeline
│   ├── training/           # Training Loop, labeling, Feature Engineering
│   ├── inference_service.py # Real-time Prediction
│   ├── feature_store.py    # Feature Management
│   └── pipeline.py         # End-to-End Pipeline
├── monitoring/             # Application Monitoring
│   ├── health_check.py     # System Health
│   └── metrics_exporter.py # Prometheus Export
├── order_manager/          # Execution Logic
│   ├── order_ledger.py     # State Tracking
│   └── smart_order.py      # [PLANNED] Advanced Order Types
├── risk/                   # Risk Management Engine
│   ├── risk_manager.py     # Main Risk Logic
│   ├── circuit_breaker.py  # Safety Switches
│   └── position_sizing.py  # Volatility Sizing
├── strategies/             # Strategy Components
│   ├── core_logic.py       # Shared Signals
│   ├── risk_mixin.py       # Risk Integration
│   └── hybrid_connector.py # [PLANNED] Websocket Bridge
├── utils/                  # Shared Utilities
│   ├── math_tools.py       # Math Helpers
│   └── logger.py           # Structured Logging
└── websocket/              # Real-Time Data Layer
    ├── aggregator.py       # Multi-Exchange Aggregation
    ├── data_stream.py      # Raw Websocket Handling
    └── exchange_handlers.py# Exchange-Specific Parsers
```

## 3. Data Flow

1.  **Input:** `src/websocket` ingests raw ticks and `src/data` loads historical candles.
2.  **Processing:**
    *   `strategies/` receives Candles (Freqtrade Loop).
    *   `src/ml/` generates probabilities.
    *   `src/websocket/aggregator.py` calculates real-time metrics (Spread, Imbalance).
3.  **Decision:** Strategy combines ML Probability + Risk Checks + Real-Time Metrics.
4.  **Execution:** `src/order_manager/` handles order placement and tracking.
5.  **Monitoring:** `src/monitoring/` pushes metrics to Prometheus.

## 4. Key Files

| File | Purpose |
|------|---------|
| `manage.py` | The main entry point for all CLI commands (train, trade, backtest). |
| `src/ml/pipeline.py` | The "Brain" - definitions of ML training and feature engineering. |
| `strategies/StoicEnsembleStrategyV5.py` | The "Body" - current production strategy. |
| `src/websocket/aggregator.py` | The "Eyes" - real-time market vision (Currently disconnected). |

## 5. Guidelines for Contributors

-   **New Strategies:** Place in `strategies/`. Must inherit from `IStrategy`.
-   **New Indicators:** Place in `src/utils/indicators.py`. Must be vectorized.
-   **New ML Models:** Register in `src/ml/training/model_registry.py`.
-   **Tests:** Mirror the `src/` structure in `tests/`. E.g., `src/risk/hrp.py` -> `tests/test_risk/test_hrp.py`.
