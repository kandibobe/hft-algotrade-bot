"""
Stoic Citadel - HashiCorp Vault Client
=======================================

Provides a client for securely fetching secrets from a HashiCorp Vault instance.
This module is intended to replace the local encryption-based SecretManager
for production deployments, enhancing security and centralizing secret management.

Usage:
    # Set environment variables:
    # VAULT_ADDR: URL of the Vault server (e.g., http://127.0.0.1:8200)
    # VAULT_TOKEN: Token for authentication with Vault

    from src.utils.vault_client import VaultClient

    # Get a specific secret
    api_key = VaultClient.get_secret("exchange/binance/api_key")

Requires the `hvac` library: pip install hvac
"""

import logging
import os
from typing import Optional

# In a real implementation, you would `import hvac`
# For now, we simulate the client to avoid dependency issues.
# from hvac import Client

logger = logging.getLogger(__name__)

class VaultClient:
    """
    A client for interacting with HashiCorp Vault.
    """
    _client = None

    @classmethod
    def _get_client(cls):
        """
        Initializes and returns a singleton Vault client instance.
        
        Reads connection details from environment variables.
        In a real scenario, this would initialize an hvac.Client.
        """
        if cls._client is None:
            vault_addr = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_addr or not vault_token:
                logger.debug("VAULT_ADDR or VAULT_TOKEN not set. VaultClient is disabled.")
                return None
            
            # This is where the real client would be initialized.
            # For demonstration, we'll use a mock/placeholder object.
            #
            # try:
            #     cls._client = hvac.Client(url=vault_addr, token=vault_token)
            #     if not cls._client.is_authenticated():
            #         raise Exception("Vault authentication failed.")
            #     logger.info(f"Successfully connected to Vault at {vault_addr}")
            # except Exception as e:
            #     logger.error(f"Failed to initialize Vault client: {e}")
            #     cls._client = None # Ensure client is None on failure
            
            # --- Mock Client for Demonstration ---
            logger.info("Using a mock Vault client for demonstration.")
            cls._client = cls._MockVaultClient(url=vault_addr, token=vault_token)
            # --- End Mock Client ---

        return cls._client

    @classmethod
    def get_secret(cls, path: str, key: str = "value") -> Optional[str]:
        """
        Retrieves a secret from Vault.

        Args:
            path: The path to the secret in the KV store (e.g., 'kv/exchange/binance').
            key: The specific key within the secret to retrieve. Defaults to 'value'.

        Returns:
            The secret value as a string, or None if not found or on error.
        """
        client = cls._get_client()
        if not client:
            return None

        try:
            # Real implementation would be:
            # response = client.secrets.kv.v2.read_secret_version(path=path)
            # secret_value = response['data']['data'].get(key)
            
            # --- Mock Response for Demonstration ---
            secret_value = client.read_secret(path, key)
            # --- End Mock Response ---

            if secret_value:
                logger.debug(f"Successfully retrieved secret from path: {path}")
            else:
                logger.warning(f"Secret key '{key}' not found at path: {path}")

            return secret_value
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault at path {path}: {e}")
            return None

    # --- Mock Client Class for Demonstration ---
    class _MockVaultClient:
        """A mock Vault client to simulate API calls without requiring hvac."""
        def __init__(self, url, token):
            self.url = url
            self.token = token
            # Pre-populate with some data for testing
            self._secrets = {
                "exchange/binance": {"api_key": "mock_binance_api_key", "secret_key": "mock_binance_secret"},
                "telegram": {"bot_token": "mock_telegram_bot_token"}
            }
            logger.info(f"Mock Vault client initialized for {url}")

        def is_authenticated(self):
            return True

        def read_secret(self, path, key):
            if path in self._secrets:
                return self._secrets[path].get(key)
            return None

def is_vault_available() -> bool:
    """
    Check if the Vault client is configured and available.
    """
    return VaultClient._get_client() is not None
