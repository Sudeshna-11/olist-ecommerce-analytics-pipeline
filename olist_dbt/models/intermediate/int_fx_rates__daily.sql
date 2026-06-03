-- Silver/intermediate: BRL->USD,EUR rates forward-filled to EVERY calendar
-- day, pivoted to one row per day. Ephemeral.
--
-- Why forward-fill: Frankfurter (ECB) only quotes on trading days, so
-- weekends/holidays have no rate. An order placed on a Saturday must still
-- get a USD/EUR value — the convention is to carry the most recent rate
-- forward. We do that with row_number() (most-recent rate_date on or before
-- each day) rather than a windowed last_value(... ignore nulls), because
-- Postgres has no IGNORE NULLS and this stays portable to Snowflake.
--
-- Days before the series starts (early 2016) resolve to null; no orders
-- fall there, so nothing real is lost.

with spine as (

    select date_day from {{ ref('dim_dates') }}

),

rates as (

    select rate_date, quote_currency, fx_rate
    from {{ ref('stg_olist__fx_rates') }}
    where base_currency = 'BRL'

),

-- for each (day, currency) rank the candidate rates by recency
day_currency as (

    select
        s.date_day,
        r.quote_currency,
        r.fx_rate,
        row_number() over (
            partition by s.date_day, r.quote_currency
            order by r.rate_date desc
        ) as recency
    from spine s
    join rates r on r.rate_date <= s.date_day

),

most_recent as (

    select date_day, quote_currency, fx_rate
    from day_currency
    where recency = 1

),

pivoted as (

    select
        date_day,
        max(case when quote_currency = 'USD' then fx_rate end)  as fx_brl_usd,
        max(case when quote_currency = 'EUR' then fx_rate end)  as fx_brl_eur
    from most_recent
    group by date_day

)

select * from pivoted
