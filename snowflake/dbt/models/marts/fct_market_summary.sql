-- Daily OHLCV summary per symbol, built on top of the staged intraday data.

with intraday as (
    select * from {{ ref('stg_intraday') }}
),

daily_agg as (
    select
        symbol,
        ts::date                                              as trade_date,
        first_value(open_price) over (
            partition by symbol, ts::date
            order by ts
        )                                                     as open_price,
        max(high_price)                                       as high_price,
        min(low_price)                                        as low_price,
        last_value(close_price) over (
            partition by symbol, ts::date
            order by ts
            rows between unbounded preceding and unbounded following
        )                                                     as close_price,
        sum(volume)                                           as total_volume,
        sum(close_price * volume) / nullif(sum(volume), 0)    as vwap,
        count(*)                                              as record_count
    from intraday
    group by symbol, ts::date, open_price, close_price
)

select distinct
    symbol,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    total_volume,
    round(vwap, 4)   as vwap,
    record_count
from daily_agg
