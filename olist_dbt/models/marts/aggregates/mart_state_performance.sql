-- Gold/aggregate: order volume, revenue, and delivery performance per
-- customer state, for the regional dashboard. Grain = one row per state.
-- Order-level (header) fact, so revenue here is gross_merchandise_brl per
-- order, not double-counted across line items.
--
-- on_time_pct is computed only over DELIVERED orders: an order is on time
-- when it reached the customer on or before the estimate. Non-delivered
-- orders are excluded from the ratio (they have no delivery date to judge).

with orders as (

    select
        c.customer_state,
        fo.gross_merchandise_brl,
        fo.is_delivered,
        fo.is_late,
        fo.delivery_days
    from {{ ref('fct_orders') }} fo
    join {{ ref('dim_customers') }} c on fo.customer_key = c.customer_key

),

agg as (

    select
        customer_state                                              as state,
        count(*)                                                    as n_orders,
        sum(gross_merchandise_brl)                                  as gmv_brl,
        avg(delivery_days)                                          as avg_delivery_days,
        sum(case when is_delivered then 1 else 0 end)               as n_delivered,
        sum(case when is_delivered and not is_late then 1 else 0 end) as n_on_time
    from orders
    group by customer_state

)

select
    state,
    n_orders,
    gmv_brl,
    cast(avg_delivery_days as numeric(6, 2))                        as avg_delivery_days,
    n_delivered,
    n_on_time,
    case when n_delivered > 0
         then cast(100.0 * n_on_time / n_delivered as numeric(5, 1))
    end                                                             as on_time_pct
from agg
