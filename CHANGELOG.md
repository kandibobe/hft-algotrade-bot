# Changelog

All notable changes to the **Stoic Citadel** project will be documented in this file.

## [2.0.0] - 2026-01-03

### 🚀 Added (Hybrid MFT Architecture)
- **Asynchronous Execution Micro-layer**: New high-performance execution engine using `AsyncIO`.
- **Smart Order Executor**: Advanced order management with `ChaseLimit` logic to minimize slippage.
- **Feast Feature Store Integration**: Production-ready feature serving for sub-millisecond ML inference.
- **Risk Gate System**: Integrated Circuit Breakers and real-time risk validation for every trade.
- **Unified Configuration**: Centralized management via `src/config/unified_config.py`.

### 🛡 Security
- **Hardened Security Rules**: Implementation of strict `.gitignore` patterns to prevent proprietary data leakage.
- **Alpha Protection**: Removal of proprietary strategies and trained models from public history.
- **Sanitized Templates**: Provided `config.json.example` and `StrategyTemplate.py` for public use.

### 📊 Monitoring & Ops
- **ELK Stack Support**: Structured JSON logging for Elasticsearch, Logstash, and Kibana.
- **Prometheus/Grafana**: New dashboards for real-time portfolio and execution monitoring.
- **Health Check System**: Automated diagnostics for environment, data, and exchange connectivity.

### 🔧 Changed
- **Directory Restructuring**: Migrated utility tools to a structured `scripts/` hierarchy.
- **Documentation Overhaul**: Institutional-grade fintech documentation and architectural guides.

## [1.0.0] - 2025-12-25
- Initial release with basic ensemble strategies.
