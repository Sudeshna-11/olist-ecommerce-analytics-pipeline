-- Gold/aggregate: revenue per product category, for the "which categories
-- drive revenue" view. Grain = one row per English category name. Products
-- without a category fall into 'unknown' rather than being dropped. An order
-- spanning two categories counts toward both — correct for category analysis.

with joined as (

    select
        coalesce(p.product_category_name_en, 'unknown')  as category,
        foi.order_id,
        p.product_id,
        foi.item_revenue_brl,
        foi.item_price_usd
    from {{ ref('fct_order_items') }} foi
    join {{ ref('dim_products') }} p on foi.product_key = p.product_key

)

select
    category,
    count(*)                        as n_items,
    count(distinct order_id)        as n_orders,
    count(distinct product_id)      as n_products,
    sum(item_revenue_brl)           as revenue_brl,
    sum(item_price_usd)             as revenue_usd
from joined
group by category
