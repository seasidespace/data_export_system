import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

import snowflake.connector
from snowflake.connector import SnowflakeConnection

from src.config import settings

logger = logging.getLogger(__name__)

_INSERT_SQL = """
    INSERT INTO {schema}.{table} (symbol, raw_data, ingested_at)
    SELECT %s, PARSE_JSON(%s), %s
"""


@contextmanager
def _snowflake_connection() -> Generator[SnowflakeConnection, None, None]:
    conn = snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=settings.snowflake_password,
        database=settings.snowflake_database,
        schema=settings.snowflake_schema,
        warehouse=settings.snowflake_warehouse,
        role=settings.snowflake_role,
    )
    try:
        yield conn
    finally:
        conn.close()


def load_raw_json(
    table: str,
    symbol: str,
    payload: dict[str, Any] | list[dict[str, Any]],
    schema: str | None = None,
) -> int:
    """Insert raw JSON into a Bronze VARIANT table.

    Returns the number of rows inserted.
    """
    schema = schema or settings.snowflake_schema
    now = datetime.now(timezone.utc).isoformat()
    json_str = json.dumps(payload)

    with _snowflake_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                _INSERT_SQL.format(schema=schema, table=table),
                (symbol, json_str, now),
            )
            conn.commit()
            row_count = cur.rowcount or 1
            logger.info(
                "Loaded %d row(s) into %s.%s for symbol %s",
                row_count,
                schema,
                table,
                symbol,
            )
            return row_count
        finally:
            cur.close()


def check_connectivity() -> bool:
    """Return True if Snowflake is reachable with the configured credentials."""
    if not settings.snowflake_account:
        return False
    try:
        with _snowflake_connection() as conn:
            conn.cursor().execute("SELECT 1")
        return True
    except Exception as exc:
        logger.warning("Snowflake connectivity check failed: %s", exc)
        return False
