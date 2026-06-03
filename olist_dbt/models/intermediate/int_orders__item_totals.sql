-- Silver/intermediate: collapse the (order_id, order_item_seq) line grain
-- down to one row per order_id. These are the header-level merchandise
-- measures that fct_orders carries. Ephemeral: this never becomes its own
-- relation — dbt inlines it wherever it's ref()'d.
--
-- gross_merchandise_brl = goods + freight, i.e. what the items side of the
-- order is "worth". It will NOT always equal the payment total (vouchers,
-- rounding, installment fees), which is exactly why we keep the two rollups
-- separate and let fct_orders expose both.

with items as (

    select * from {{ ref('stg_olist__order_items') }}

),

aggregated as (

    select
        order_id,
        count(*)                                  as n_items,
        count(distinct seller_id)                 as n_sellers,
        count(distinct product_id)                as n_products,
        sum(item_price_brl)                       as total_item_price_brl,
        sum(freight_brl)                          as total_freight_brl,
        sum(item_price_brl) + sum(freight_brl)    as gross_merchandise_brl
    from items
    group by order_id

)

select * from aggregated
