-- Bronze tables: raw VARIANT storage
USE DATABASE MARKET_ANALYTICS;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS raw_intraday (
    id              INT AUTOINCREMENT PRIMARY KEY,
    symbol          VARCHAR(10)   NOT NULL,
    raw_data        VARIANT       NOT NULL,
    ingested_at     TIMESTAMP_TZ  NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS raw_crypto_daily (
    id              INT AUTOINCREMENT PRIMARY KEY,
    symbol          VARCHAR(10)   NOT NULL,
    raw_data        VARIANT       NOT NULL,
    ingested_at     TIMESTAMP_TZ  NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS raw_overview (
    id              INT AUTOINCREMENT PRIMARY KEY,
    symbol          VARCHAR(10)   NOT NULL,
    raw_data        VARIANT       NOT NULL,
    ingested_at     TIMESTAMP_TZ  NOT NULL DEFAULT CURRENT_TIMESTAMP()
);
