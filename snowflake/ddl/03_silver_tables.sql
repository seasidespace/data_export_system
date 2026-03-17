-- Silver tables: flattened, typed columns
-- These are the targets of dbt models; DDL here for reference / initial setup.
USE DATABASE MARKET_ANALYTICS;
USE SCHEMA TRANSFORMED;

CREATE TABLE IF NOT EXISTS stg_intraday (
    symbol          VARCHAR(10)   NOT NULL,
    ts              TIMESTAMP_NTZ NOT NULL,
    open_price      NUMBER(18,4),
    high_price      NUMBER(18,4),
    low_price       NUMBER(18,4),
    close_price     NUMBER(18,4),
    volume          BIGINT,
    ingested_at     TIMESTAMP_TZ  NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_market_summary (
    symbol          VARCHAR(10)   NOT NULL,
    trade_date      DATE          NOT NULL,
    open_price      NUMBER(18,4),
    high_price      NUMBER(18,4),
    low_price       NUMBER(18,4),
    close_price     NUMBER(18,4),
    total_volume    BIGINT,
    vwap            NUMBER(18,4),
    record_count    INT,
    UNIQUE (symbol, trade_date)
);
