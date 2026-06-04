-- Gold/aggregate: revenue per calendar day, for the executive time-series
-- dashboard. Grain = one row per day that had activity. Built from the
-- line-item fact (the revenue grain) and enriched with calendar attributes
-- so Power BI can slice by month/quarter/weekend without its own date logic.

with items as (

    select
        purchase_date_key,
        count(distinct order_id)        as n_orders,
        count(*)                        as n_items,
        count(distinct seller_key)      as n_sellers,
        sum(item_price_brl)             as items_brl,
        sum(freight_brl)                as freight_brl,
        sum(item_revenue_brl)           as gmv_brl,
        sum(item_price_usd)             as items_usd,
        sum(item_price_eur)             as items_eur
    from {{ ref('fct_order_items') }}
    group by purchase_date_key

)

select
    d.date_key,
    d.date_day,
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    d.is_weekend,

    i.n_orders,
    i.n_items,
    i.n_sellers,
    i.items_brl,
    i.freight_brl,
    i.gmv_brl,
    i.items_usd,
    i.items_eur

from items i
join {{ ref('dim_dates') }} d on i.purchase_date_key = d.date_key
