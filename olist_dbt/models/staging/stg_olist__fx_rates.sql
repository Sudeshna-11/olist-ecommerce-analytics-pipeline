-- Silver: daily BRL->USD,EUR FX rates from Frankfurter (ECB).
-- Long format, composite PK = (rate_date, base_currency, quote_currency).
-- Used in marts to express revenue in USD/EUR alongside the BRL native.

with source as (

    select * from {{ source('olist_raw', 'raw_fx_rates') }}

),

renamed as (

    select
        cast(rate_date as date)              as rate_date,
        cast(base_currency as varchar)       as base_currency,
        cast(quote_currency as varchar)      as quote_currency,
        cast(rate as numeric(18, 8))         as fx_rate
    from source

)

select * from renamed
