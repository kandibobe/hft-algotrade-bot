# Quick Start

This guide will help you run the bot for the first time.

## 1. Dry-Run Mode

It is highly recommended to start in Dry-Run mode to test your configuration and strategy without risking real funds.

```bash
freqtrade trade --config config.json --strategy YourStrategy
```

## 2. Live Trading

Once you are confident with your setup, you can start live trading by disabling the `dry_run` option in your `config.json` file.

```json
{
    "dry_run": false,
    ...
}
```

Then, run the same command as before:

```bash
freqtrade trade --config config.json --strategy YourStrategy
```

## 3. Using the Telegram Bot

The Telegram bot allows you to monitor and control your bot from anywhere. Refer to the **[Telegram Bot](telegram.md)** guide for setup instructions.
