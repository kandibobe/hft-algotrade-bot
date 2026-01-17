# How-To: Risk Management Configuration

Proper risk management is critical for the survival of any automated trading system. Stoic Citadel provides a multi-layered risk protection system.

## 1. Global Risk Settings

All global risk settings are defined in your configuration file (e.g., `user_data/config/config_production.json`) under the `risk_options` key.

```json
"risk_options": {
    "max_drawdown": 0.15,
    "max_leverage": 3.0,
    "circuit_breaker_threshold": 0.05,
    "emergency_stop_enabled": true
}
```

## 2. Setting Up Circuit Breakers

Circuit breakers automatically pause trading if specific loss thresholds are hit within a short period.

1.  **Define the threshold:** In your config, set `circuit_breaker_threshold` (e.g., `0.05` for 5%).
2.  **Monitor Status:** Use the Telegram bot command `/health` to check if any circuit breakers have been tripped.
3.  **Reset:** Circuit breakers usually reset automatically after a cooldown period, but can be manually reset via the Telegram bot or the management script.

## 3. Position Sizing

Stoic Citadel uses dynamic position sizing based on account volatility and risk per trade.

- **Risk per Trade:** Set in the strategy file or config.
- **HRP (Hierarchical Risk Parity):** Enabled via `use_hrp: true` in the config for advanced portfolio allocation.

## 4. Emergency Procedures

### Manual Kill-Switch
If you need to stop the bot and close all positions immediately:
- **Telegram:** Send the `/stop` command followed by `/emergency_liquidate`.
- **CLI:** Run `python scripts/maintenance/full_cycle_launch.py --action stop`.

### Automatic Liquidation
If the `max_drawdown` is exceeded, the system will automatically enter "Safe Mode," canceling all open orders and preventing new entries.
