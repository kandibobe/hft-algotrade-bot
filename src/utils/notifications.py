"""
Stoic Citadel - Notification System
====================================

Handles multi-channel notifications (Telegram, Slack, Email).
"""

import logging
import requests
import os
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Notifier:
    """Central notification manager."""
    
    def __init__(self):
        self.telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram notifications not configured in environment")
            
    def send_notification(self, message: str, level: str = "info") -> bool:
        """
        Send notification to configured channels.
        
        Args:
            message: Message text
            level: info, warning, critical
            
        Returns:
            True if at least one channel succeeded
        """
        # Add emoji based on level
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }.get(level, "")
        
        full_message = f"{emoji} {message}"
        
        success = False
        
        # 1. Telegram
        if self.telegram_token and self.telegram_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": full_message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    success = True
                else:
                    logger.error(f"Telegram API error: {response.text}")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")
                
        # 2. Slack
        if self.slack_webhook:
            try:
                payload = {"text": full_message}
                response = requests.post(self.slack_webhook, json=payload, timeout=10)
                if response.status_code == 200:
                    success = True
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")
                
        # 3. Always Log
        if level == "critical":
            logger.critical(full_message)
        elif level == "warning":
            logger.warning(full_message)
        else:
            logger.info(full_message)
            
        return success

_notifier_instance = None

def get_notifier() -> Notifier:
    """Global notifier access."""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = Notifier()
    return _notifier_instance
