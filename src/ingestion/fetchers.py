import logging
from typing import Any

from src.config import settings
from src.ingestion.client import get_client
from src.ingestion.rate_limiter import smart_retry

logger = logging.getLogger(__name__)


@smart_retry()
async def fetch_intraday(symbol: str, interval: str = "1min") -> dict[str, Any]:
    """Fetch TIME_SERIES_INTRADAY data for a given equity symbol."""
    client = await get_client()
    resp = await client.get(
        "",
        params={
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": settings.alpha_vantage_api_key,
            "outputsize": "compact",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("Fetched intraday data for %s (%d bytes)", symbol, len(resp.content))
    return data


@smart_retry()
async def fetch_crypto_daily(symbol: str, market: str = "USD") -> dict[str, Any]:
    """Fetch DIGITAL_CURRENCY_DAILY data for a given crypto symbol."""
    client = await get_client()
    resp = await client.get(
        "",
        params={
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
            "apikey": settings.alpha_vantage_api_key,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("Fetched crypto daily data for %s (%d bytes)", symbol, len(resp.content))
    return data


@smart_retry()
async def fetch_overview(symbol: str) -> dict[str, Any]:
    """Fetch OVERVIEW (fundamental data) for a given equity symbol."""
    client = await get_client()
    resp = await client.get(
        "",
        params={
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_api_key,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("Fetched overview data for %s (%d bytes)", symbol, len(resp.content))
    return data
