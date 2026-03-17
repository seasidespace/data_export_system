from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DataType(str, Enum):
    INTRADAY = "intraday"
    CRYPTO = "crypto"
    OVERVIEW = "overview"


class IngestRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1, examples=[["AAPL", "MSFT"]])
    data_type: DataType
    interval: str = Field(default="1min", pattern=r"^(1|5|15|30|60)min$")


class IntradayPrice(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class CryptoDailyPrice(BaseModel):
    timestamp: datetime
    open_usd: float
    high_usd: float
    low_usd: float
    close_usd: float
    volume: float
    market_cap_usd: float


class CompanyOverview(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None


class IngestionResult(BaseModel):
    symbol: str
    data_type: DataType
    records_loaded: int
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    api_reachable: bool
    snowflake_connected: bool
    last_ingestion: datetime | None = None
