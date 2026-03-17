# Real-Time Market Analytics Engine

An end-to-end ETL pipeline that ingests real-time financial data (Equities, Crypto, Forex fundamentals) from Alpha Vantage into a Snowflake data warehouse. Built for resilience with smart rate-limiting, async I/O, and self-healing orchestration.

## Architecture

```
Alpha Vantage API
        │
        ▼
┌──────────────────────┐
│  FastAPI Ingestor     │  ← Phase 1 (fully implemented)
│  • Token-bucket limiter│
│  • httpx async client  │
│  • Smart retry logic   │
└──────────┬───────────┘
           │  batch INSERT (VARIANT)
           ▼
┌──────────────────────┐
│  Snowflake           │  ← Phase 2 (DDL + dbt scaffolded)
│  • Bronze: raw JSON  │
│  • Silver: typed     │
│    via dbt models    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Airflow / Dashboard │  ← Phase 3 (scaffolded)
│  • Scheduled DAGs    │
│  • Health monitoring │
└──────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Alpha Vantage API key ([free tier](https://www.alphavantage.co/support/#api-key))
- Snowflake account (optional for local dev — ingestion works without it)

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API key and Snowflake credentials
```

### 2. Run with Docker

```bash
docker compose up --build
```

The ingestor will be available at `http://localhost:8000`.

### 3. Run Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## API Endpoints

### `POST /ingest`

Trigger ingestion for one or more symbols.

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"], "data_type": "intraday"}'
```

**Supported `data_type` values:**

| Value       | Alpha Vantage Function      | Description                    |
|-------------|-----------------------------|--------------------------------|
| `intraday`  | `TIME_SERIES_INTRADAY`      | 1-min equity prices            |
| `crypto`    | `DIGITAL_CURRENCY_DAILY`    | Daily crypto OHLCV             |
| `overview`  | `OVERVIEW`                  | Company fundamentals           |

### `GET /health`

Returns API reachability, Snowflake connectivity, and last ingestion timestamp.

```bash
curl http://localhost:8000/health
```

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
├── src/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # pydantic-settings configuration
│   ├── ingestion/
│   │   ├── client.py            # httpx async client with connection pooling
│   │   ├── rate_limiter.py      # Token-bucket + @smart_retry decorator
│   │   ├── fetchers.py          # Per-endpoint async fetchers
│   │   └── schemas.py           # Pydantic request/response models
│   ├── loading/
│   │   └── snowflake_loader.py  # Snowflake VARIANT column batch loader
│   └── api/
│       └── routes.py            # /ingest and /health routes
├── snowflake/
│   ├── ddl/                     # Database, Bronze, and Silver DDL scripts
│   └── dbt/                     # dbt project with staging + mart models
├── airflow/
│   ├── dags/                    # Market ingestion DAG with recovery task
│   └── docker-compose.airflow.yml
├── dashboard/                   # Phase 3 React dashboard (scaffold)
├── tests/                       # pytest + respx test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Roadmap

- [x] **Phase 1** — Robust Ingestor (async, rate-limited, Snowflake loading)
- [ ] **Phase 2** — Snowflake Warehouse (run DDL, wire dbt models to live data)
- [ ] **Phase 3** — Visibility Layer (Airflow scheduling, React health dashboard)
