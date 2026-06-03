-- Gold/fact: one row per order line (order_id, order_item_seq). This is
-- the revenue grain — product- and seller-level analysis lives here, as
-- opposed to the header-level fct_orders.
--
-- Materialized INCREMENTAL: on a normal run dbt only processes lines from
-- orders purchased after the latest purchase already loaded (high-water
-- mark on purchased_at). unique_key + delete+insert make re-runs idempotent
-- if a late-arriving order lands inside the window.
--
-- Conformed dimensions are joined by SURROGATE key (product_key, seller_key,
-- customer_key, purchase_date_key) — the Kimball-correct fact-to-dim wiring.
-- dim_products is joined POINT-IN-TIME: the product version whose validity
-- window contains the order's purchase timestamp (see dim_products for the
-- floored initial valid_from that makes backdated orders resolve).
--
-- FX: BRL is native; USD/EUR are derived from the forward-filled daily rate
-- via the convert_brl macro.

{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='delete+insert'
    )
}}

with items as (

    select * from {{ ref('stg_olist__order_items') }}

),

orders as (

    select order_id, customer_id, order_status, purchased_at
    from {{ ref('stg_olist__orders') }}

),

fx_daily as (

    select * from {{ ref('int_fx_rates__daily') }}

),

joined as (

    select
        i.order_id,
        i.order_item_seq,
        o.order_status,
        o.purchased_at,
        i.shipping_limit_at,

        -- conformed-dimension surrogate keys
        p.product_key,
        s.seller_key,
        c.customer_key,
        cast(extract(year  from o.purchased_at) * 10000
             + extract(month from o.purchased_at) * 100
             + extract(day   from o.purchased_at) as integer)    as purchase_date_key,

        -- measures (native BRL)
        i.item_price_brl,
        i.freight_brl,

        -- joined daily FX rates (forward-filled)
        fx.fx_brl_usd,
        fx.fx_brl_eur

    from items i
    join orders o
        on i.order_id = o.order_id

    -- point-in-time: the product version in effect at purchase time
    left join {{ ref('dim_products') }} p
        on  i.product_id = p.product_id
        and o.purchased_at >= p.valid_from
        and (p.valid_to is null or o.purchased_at < p.valid_to)

    left join {{ ref('dim_sellers') }} s
        on i.seller_id = s.seller_id

    left join {{ ref('dim_customers') }} c
        on o.customer_id = c.customer_id

    left join fx_daily fx
        on fx.date_day = cast(o.purchased_at as date)

)

select
    {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_seq']) }}  as order_item_key,

    order_id,
    order_item_seq,
    order_status,
    purchased_at,
    shipping_limit_at,

    product_key,
    seller_key,
    customer_key,
    purchase_date_key,

    item_price_brl,
    freight_brl,
    item_price_brl + freight_brl                          as item_revenue_brl,

    {{ convert_brl('item_price_brl', 'fx_brl_usd') }}     as item_price_usd,
    {{ convert_brl('item_price_brl', 'fx_brl_eur') }}     as item_price_eur

from joined

{% if is_incremental() %}
where purchased_at > (select max(purchased_at) from {{ this }})
{% endif %}
