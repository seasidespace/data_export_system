-- Market Analytics: database and schema setup
-- Run once with SYSADMIN (or equivalent) role

CREATE DATABASE IF NOT EXISTS MARKET_ANALYTICS;
USE DATABASE MARKET_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Bronze layer – raw JSON from Alpha Vantage';

CREATE SCHEMA IF NOT EXISTS TRANSFORMED
    COMMENT = 'Silver layer – cleaned, typed tables built by dbt';
