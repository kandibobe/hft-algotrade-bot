"""
Alternative Data Fetcher
========================

Fetches data from alternative sources like sentiment analysis APIs, on-chain data, etc.
"""

import logging
import httpx
from typing import Any, Dict

logger = logging.getLogger(__name__)

class AlternativeDataFetcher:
    """
    A class to fetch data from various alternative sources.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self.http_client = http_client or httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    async def fetch_fear_and_greed_index(self) -> Dict[str, Any]:
        """
        Fetches the Fear and Greed Index from api.alternative.me.
        """
        url = "https://api.alternative.me/fng/?limit=1"
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                 return data['data'][0]
            return {}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Fear and Greed Index: {e}")
            return {}
        except Exception as e:
            logger.error(f"An error occurred while fetching Fear and Greed Index: {e}")
            return {}

    async def fetch_crypto_news_sentiment(self, symbol: str) -> float:
        """
        Fetches news sentiment for a specific symbol.
        
        Strategy:
        1. (Future) Use Paid API if configured (e.g. CryptoPanic).
        2. (Current) Fallback to Fear & Greed Index normalization as a global sentiment proxy.
           This is free, reliable, and provides a decent "market mood" baseline.
        
        Returns a score from -1.0 (Bearish) to 1.0 (Bullish).
        """
        logger.info(f"Fetching news sentiment proxy for {symbol}...")
        
        # Fallback: Use Fear & Greed Index as general market sentiment proxy
        fng_data = await self.fetch_fear_and_greed_index()
        if fng_data and 'value' in fng_data:
            try:
                # Normalize 0-100 to -1.0 to 1.0
                # 0 -> -1.0 (Extreme Fear)
                # 50 -> 0.0 (Neutral)
                # 100 -> 1.0 (Extreme Greed)
                fng_value = float(fng_data['value'])
                sentiment_score = (fng_value - 50) / 50.0
                
                # Clip just in case
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
                
                logger.debug(f"Sentiment derived from F&G ({fng_value}): {sentiment_score:.2f}")
                return sentiment_score
            except (ValueError, TypeError) as e:
                 logger.warning(f"Error parsing F&G value: {e}")

        # Absolute fallback
        return 0.0 

async def get_fear_and_greed_index() -> Dict[str, Any]:
    """
    Convenience function to fetch the Fear and Greed Index.
    """
    async with AlternativeDataFetcher() as fetcher:
        return await fetcher.fetch_fear_and_greed_index()
