-- Gold/aggregate: revenue, volume, and review rating per seller, for the
-- seller-performance view. Grain = one row per seller.
--
-- Revenue/volume come from the line-item fact. The rating is the average
-- review score across the orders a seller participated in: reviews are at
-- the order grain, so we map them in through distinct (seller, order) pairs.
-- An order with two sellers contributes its review to both — acceptable for
-- a seller-level rating.

with item_agg as (

    select
        seller_key,
        count(distinct order_id)    as n_orders,
        count(*)                    as n_items,
        sum(item_revenue_brl)       as revenue_brl,
        sum(item_price_usd)         as revenue_usd
    from {{ ref('fct_order_items') }}
    group by seller_key

),

seller_orders as (

    select distinct seller_key, order_id
    from {{ ref('fct_order_items') }}

),

review_agg as (

    select
        so.seller_key,
        avg(r.review_score)         as avg_review_score,
        count(r.review_key)         as n_reviews
    from seller_orders so
    join {{ ref('fct_order_reviews') }} r on so.order_id = r.order_id
    group by so.seller_key

)

select
    s.seller_key,
    s.seller_id,
    s.seller_state,
    s.seller_city,

    i.n_orders,
    i.n_items,
    i.revenue_brl,
    i.revenue_usd,

    cast(rv.avg_review_score as numeric(4, 2))  as avg_review_score,
    coalesce(rv.n_reviews, 0)                   as n_reviews

from item_agg i
join {{ ref('dim_sellers') }} s on i.seller_key = s.seller_key
left join review_agg rv on i.seller_key = rv.seller_key
