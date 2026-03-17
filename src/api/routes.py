import asyncio
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException

from src.config import settings
from src.ingestion.fetchers import fetch_crypto_daily, fetch_intraday, fetch_overview
from src.ingestion.schemas import DataType, HealthResponse, IngestRequest, IngestionResult
from src.loading.snowflake_loader import check_connectivity, load_raw_json

logger = logging.getLogger(__name__)
router = APIRouter()

_TABLE_MAP: dict[DataType, str] = {
    DataType.INTRADAY: "raw_intraday",
    DataType.CRYPTO: "raw_crypto_daily",
    DataType.OVERVIEW: "raw_overview",
}

_FETCHER_MAP = {
    DataType.INTRADAY: fetch_intraday,
    DataType.CRYPTO: fetch_crypto_daily,
    DataType.OVERVIEW: fetch_overview,
}

_last_successful_ingestion: datetime | None = None


@router.post("/ingest", response_model=list[IngestionResult])
async def ingest(request: IngestRequest):
    """Trigger ingestion for a list of symbols and a given data type."""
    global _last_successful_ingestion

    fetcher = _FETCHER_MAP[request.data_type]
    table = _TABLE_MAP[request.data_type]
    results: list[IngestionResult] = []

    for symbol in request.symbols:
        try:
            if request.data_type == DataType.INTRADAY:
                data = await fetcher(symbol, interval=request.interval)
            else:
                data = await fetcher(symbol)

            try:
                rows = load_raw_json(table=table, symbol=symbol, payload=data)
            except Exception as sf_err:
                logger.warning("Snowflake load skipped for %s: %s", symbol, sf_err)
                rows = 0

            _last_successful_ingestion = datetime.now(timezone.utc)
            results.append(
                IngestionResult(
                    symbol=symbol,
                    data_type=request.data_type,
                    records_loaded=rows,
                )
            )
            logger.info("Ingested %s (%s) — %d rows loaded", symbol, request.data_type.value, rows)

        except Exception as exc:
            logger.error("Failed to ingest %s: %s", symbol, exc)
            results.append(
                IngestionResult(
                    symbol=symbol,
                    data_type=request.data_type,
                    records_loaded=0,
                    success=False,
                    error=str(exc),
                )
            )

    return results


@router.get("/health", response_model=HealthResponse)
async def health():
    """Return service health including API reachability and Snowflake connectivity."""
    api_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                settings.alpha_vantage_base_url,
                params={"function": "TIME_SERIES_INTRADAY", "symbol": "IBM", "interval": "1min", "apikey": "demo"},
            )
            api_ok = resp.status_code == 200
    except Exception:
        pass

    sf_ok = await asyncio.to_thread(check_connectivity)

    status = "healthy" if api_ok else "degraded"
    return HealthResponse(
        status=status,
        api_reachable=api_ok,
        snowflake_connected=sf_ok,
        last_ingestion=_last_successful_ingestion,
    )
