# Contributing to Stoic Citadel 🏛️

First off, thank you for considering contributing to Stoic Citadel! It's people like you that make this project better.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct
This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs
Before creating bug reports, please check existing issues. Use our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).

### 💡 Suggesting Features
Feature requests are welcome! Use our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose
- `make` utility

### 2. Environment Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mft-algotrade-bot.git
cd mft-algotrade-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest pre-commit

# Install pre-commit hooks
pre-commit install
```

### 3. Local Development Stack
```bash
# Start Redis and Postgres for development
docker-compose up -d redis postgres
```

---

## 📝 Style Guidelines

### Python Code Style
- **Formatter**: Black (line length: 88)
- **Linter**: Flake8
- **Type Checker**: MyPy (Strict mode preferred for core modules)
- **Docstrings**: Google style

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code restructuring
- `test:` for adding/fixing tests

---

## 🔄 Pull Request Process

1. **Fork** the repository and create your branch from `main`.
2. **Implement** your changes and add tests.
3. **Run Validation**:
   ```bash
   make lint
   make test
   ```
4. **Update** documentation in `docs/` or `README.md` if applicable.
5. **Submit** PR using the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).

### PR Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Lint checks pass (`make lint`)
- [ ] Risk management limits remain intact

---

## ⚠️ Institutional Safety Rules

### Risk Core (CRITICAL)
NEVER modify files in `src/risk/` or risk-related parameters in `unified_config.py` without extensive backtesting and community discussion. Any PR touching the Risk Core will undergo rigorous audit.

### Latency Sensitivity
Avoid introducing blocking I/O or heavy computations in the Micro Layer (`src/websocket/`, `src/order_manager/`).

---

Thank you for contributing to the future of open-source algorithmic trading! 🎉
