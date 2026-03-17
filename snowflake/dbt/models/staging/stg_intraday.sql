-- Flatten raw intraday JSON from Bronze into typed columns.
-- Each raw_data VARIANT contains a nested "Time Series (Xmin)" object keyed by timestamp.

with source as (
    select
        id                  as raw_id,
        symbol,
        raw_data,
        ingested_at
    from {{ source('raw', 'raw_intraday') }}
),

flattened as (
    select
        s.symbol,
        f.key::timestamp_ntz                                  as ts,
        f.value:"1. open"::number(18,4)                       as open_price,
        f.value:"2. high"::number(18,4)                       as high_price,
        f.value:"3. low"::number(18,4)                        as low_price,
        f.value:"4. close"::number(18,4)                      as close_price,
        f.value:"5. volume"::bigint                           as volume,
        s.ingested_at
    from source s,
    lateral flatten(input => s.raw_data:"Time Series (1min)") f
)

select * from flattened
