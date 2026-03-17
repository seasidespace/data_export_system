import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.ingestion.client import close_client, get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_client()
    logging.getLogger(__name__).info("HTTP client initialised")
    yield
    await close_client()
    logging.getLogger(__name__).info("HTTP client closed")


app = FastAPI(
    title="Market Analytics Ingestor",
    description="Real-time financial data ingestion engine for Alpha Vantage → Snowflake",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
