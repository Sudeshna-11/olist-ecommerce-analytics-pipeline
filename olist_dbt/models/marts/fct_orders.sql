-- Gold/fact: one row per order_id (header grain). Status + delivery
-- cycle-times + merchandise and payment rollups. This is the "how the
-- order behaved as a whole" fact; per-line revenue analysis lives in the
-- finer-grained fct_order_items (built next).
--
-- order_id is a degenerate dimension (kept on the fact, no dim table).
-- customer_key is the surrogate FK to dim_customers (resolved via the
-- order's natural customer_id) — kept consistent with fct_order_items so
-- every fact wires to the conformed dims the same way. purchase_date_key
-- joins to dim_dates.date_key.
--
-- Null-safety: a small number of orders have no line items and/or no
-- payment record, so the rollups are left-joined and counts/sums coalesced
-- to 0. Delivery measures are deliberately left null for orders that never
-- reached the customer (delivered_to_customer_at is null) — a null cycle
-- time is the honest value, not zero.

with orders as (

    select * from {{ ref('stg_olist__orders') }}

),

item_totals as (

    select * from {{ ref('int_orders__item_totals') }}

),

payment_totals as (

    select * from {{ ref('int_orders__payment_totals') }}

),

final as (

    select
        -- keys
        o.order_id,
        c.customer_key,
        cast(extract(year  from o.purchased_at) * 10000
             + extract(month from o.purchased_at) * 100
             + extract(day   from o.purchased_at) as integer)            as purchase_date_key,

        -- status + flags
        o.order_status,
        o.is_delivered,
        o.is_late,

        -- lifecycle timestamps
        o.purchased_at,
        o.approved_at,
        o.delivered_to_carrier_at,
        o.delivered_to_customer_at,
        o.estimated_delivery_at,

        -- delivery cycle-time measures, in days. dbt.datediff is core's
        -- cross-backend shim (adapter-dispatched), so this compiles on both
        -- Postgres and Snowflake.
        {{ dbt.datediff('o.purchased_at', 'o.delivered_to_customer_at', 'day') }}        as delivery_days,
        {{ dbt.datediff('o.purchased_at', 'o.estimated_delivery_at', 'day') }}           as estimated_delivery_days,
        {{ dbt.datediff('o.delivered_to_customer_at', 'o.estimated_delivery_at', 'day') }} as delivery_vs_estimate_days,

        -- merchandise rollup (from line items)
        coalesce(i.n_items, 0)                  as n_items,
        coalesce(i.n_sellers, 0)                as n_sellers,
        coalesce(i.n_products, 0)               as n_products,
        coalesce(i.total_item_price_brl, 0)     as total_item_price_brl,
        coalesce(i.total_freight_brl, 0)        as total_freight_brl,
        coalesce(i.gross_merchandise_brl, 0)    as gross_merchandise_brl,

        -- payment rollup
        coalesce(p.n_payment_records, 0)        as n_payment_records,
        coalesce(p.n_payment_types, 0)          as n_payment_types,
        p.max_installments,
        coalesce(p.total_payment_brl, 0)        as total_payment_brl

    from orders o
    left join {{ ref('dim_customers') }} c on o.customer_id = c.customer_id
    left join item_totals    i on o.order_id = i.order_id
    left join payment_totals p on o.order_id = p.order_id

)

select * from final
