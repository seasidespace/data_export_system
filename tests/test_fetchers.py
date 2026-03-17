import pytest
import pytest_asyncio
import respx
from httpx import Response

from src.ingestion.client import close_client
from src.ingestion.fetchers import fetch_crypto_daily, fetch_intraday, fetch_overview
from src.ingestion.rate_limiter import TokenBucket

AV_URL = "https://www.alphavantage.co/query/"


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_client():
    yield
    await close_client()


@pytest.fixture(autouse=True)
def _fast_bucket(monkeypatch):
    """Replace the default bucket with a permissive one so tests don't wait."""
    fast = TokenBucket(max_tokens=100, refill_period=1)
    monkeypatch.setattr("src.ingestion.rate_limiter._default_bucket", fast)


SAMPLE_INTRADAY = {
    "Meta Data": {
        "1. Information": "Intraday (1min) prices",
        "2. Symbol": "AAPL",
    },
    "Time Series (1min)": {
        "2026-03-16 16:00:00": {
            "1. open": "175.00",
            "2. high": "176.00",
            "3. low": "174.50",
            "4. close": "175.50",
            "5. volume": "1234567",
        }
    },
}

SAMPLE_CRYPTO = {
    "Meta Data": {"2. Digital Currency Code": "BTC"},
    "Time Series (Digital Currency Daily)": {
        "2026-03-16": {
            "1a. open (USD)": "65000.00",
            "2a. high (USD)": "66000.00",
            "3a. low (USD)": "64000.00",
            "4a. close (USD)": "65500.00",
            "5. volume": "12345.67",
            "6. market cap (USD)": "1200000000000",
        }
    },
}

SAMPLE_OVERVIEW = {
    "Symbol": "AAPL",
    "Name": "Apple Inc",
    "Exchange": "NASDAQ",
    "Sector": "Technology",
    "MarketCapitalization": "2800000000000",
    "PERatio": "28.5",
    "EPS": "6.15",
}


@pytest.mark.asyncio
@respx.mock
async def test_fetch_intraday_parses_response():
    respx.get(AV_URL).mock(return_value=Response(200, json=SAMPLE_INTRADAY))

    data = await fetch_intraday("AAPL")

    assert "Meta Data" in data
    assert "Time Series (1min)" in data


@pytest.mark.asyncio
@respx.mock
async def test_fetch_crypto_daily_parses_response():
    respx.get(AV_URL).mock(return_value=Response(200, json=SAMPLE_CRYPTO))

    data = await fetch_crypto_daily("BTC")

    assert "Meta Data" in data
    assert "Time Series (Digital Currency Daily)" in data


@pytest.mark.asyncio
@respx.mock
async def test_fetch_overview_parses_response():
    respx.get(AV_URL).mock(return_value=Response(200, json=SAMPLE_OVERVIEW))

    data = await fetch_overview("AAPL")

    assert data["Symbol"] == "AAPL"
    assert data["Name"] == "Apple Inc"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_intraday_raises_on_http_error():
    respx.get(AV_URL).mock(return_value=Response(500, text="Internal Server Error"))

    with pytest.raises(Exception):
        await fetch_intraday("AAPL")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_intraday_retries_on_throttle():
    route = respx.get(AV_URL)
    route.side_effect = [
        Response(200, json={"Note": "API call frequency exceeded"}),
        Response(200, json=SAMPLE_INTRADAY),
    ]

    data = await fetch_intraday("AAPL")
    assert "Time Series (1min)" in data
