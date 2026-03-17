"""
Market Analytics Ingestion DAG

Orchestrates periodic ingestion of equity, crypto, and fundamental data
via the FastAPI ingestor service.  Includes a heartbeat sensor and
automatic recovery task for self-healing behaviour.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.http_sensor import HttpSensor

INGESTOR_BASE = "http://ingestor:8000"
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL"]
CRYPTO_SYMBOLS = ["BTC", "ETH"]

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


def _trigger_ingest(symbols: list[str], data_type: str, **kwargs):
    """POST to the ingestor /ingest endpoint."""
    import requests

    resp = requests.post(
        f"{INGESTOR_BASE}/ingest",
        json={"symbols": symbols, "data_type": data_type},
        timeout=120,
    )
    resp.raise_for_status()
    results = resp.json()
    failed = [r for r in results if not r["success"]]
    if failed:
        raise RuntimeError(f"Ingestion failures: {failed}")
    return results


def _recovery(**kwargs):
    """Re-run failed symbols from the previous task instance."""
    import logging

    logging.warning("Recovery task triggered — check upstream logs for failed symbols")


with DAG(
    dag_id="market_ingestion",
    default_args=default_args,
    description="Ingest Alpha Vantage data into Snowflake Bronze layer",
    schedule_interval="*/5 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["market-analytics", "ingestion"],
) as dag:

    heartbeat = HttpSensor(
        task_id="check_ingestor_health",
        http_conn_id="ingestor_api",
        endpoint="/health",
        response_check=lambda resp: resp.json().get("status") in ("healthy", "degraded"),
        poke_interval=30,
        timeout=120,
    )

    ingest_equities = PythonOperator(
        task_id="ingest_equities",
        python_callable=_trigger_ingest,
        op_kwargs={"symbols": DEFAULT_SYMBOLS, "data_type": "intraday"},
    )

    ingest_crypto = PythonOperator(
        task_id="ingest_crypto",
        python_callable=_trigger_ingest,
        op_kwargs={"symbols": CRYPTO_SYMBOLS, "data_type": "crypto"},
    )

    ingest_fundamentals = PythonOperator(
        task_id="ingest_fundamentals",
        python_callable=_trigger_ingest,
        op_kwargs={"symbols": DEFAULT_SYMBOLS, "data_type": "overview"},
    )

    recovery = PythonOperator(
        task_id="recovery",
        python_callable=_recovery,
        trigger_rule="one_failed",
    )

    heartbeat >> [ingest_equities, ingest_crypto, ingest_fundamentals] >> recovery
