import httpx

from src.config import settings

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.alpha_vantage_base_url,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
