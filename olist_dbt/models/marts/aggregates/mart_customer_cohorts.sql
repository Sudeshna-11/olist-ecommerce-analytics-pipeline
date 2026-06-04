-- Gold/aggregate: monthly acquisition cohorts and repeat-purchase behaviour,
-- for the customer-retention view. Grain = one row per acquisition cohort —
-- the calendar month of a customer's FIRST order.
--
-- The Olist identity quirk drives this model: customer_id is per-ORDER (a
-- returning shopper gets a brand-new one on every order), while
-- customer_unique_id is the stable person. Repeat-purchase must therefore be
-- counted over customer_unique_id, resolved through dim_customers — counting
-- customer_id would make every shopper look new and the repeat rate ~0.
--
-- Revenue is GMV (goods + freight) per order from the header fact, summed to
-- the customer and then the cohort, so the CLV here is GMV-grade and
-- reconciles with the gmv_brl exposed by the other marts. All placed orders
-- count (status not filtered) — a placed order is purchase intent regardless
-- of later cancellation.

with orders as (

    select
        c.customer_unique_id,
        o.purchased_at,
        o.gross_merchandise_brl
    from {{ ref('fct_orders') }} o
    join {{ ref('dim_customers') }} c on o.customer_key = c.customer_key

),

per_customer as (

    -- collapse the per-order identities down to the real shopper: their
    -- acquisition month (first purchase), lifetime order count, lifetime GMV
    select
        customer_unique_id,
        cast(date_trunc('month', min(purchased_at)) as date)  as cohort_month,
        count(*)                                              as n_orders,
        sum(gross_merchandise_brl)                            as customer_gmv_brl
    from orders
    group by customer_unique_id

)

select
    cohort_month,
    count(*)                                                  as n_customers,
    sum(case when n_orders > 1 then 1 else 0 end)             as n_repeat_customers,
    cast(100.0 * sum(case when n_orders > 1 then 1 else 0 end) / count(*)
         as numeric(5, 1))                                    as repeat_rate_pct,
    sum(n_orders)                                             as total_orders,
    cast(avg(n_orders) as numeric(6, 2))                      as avg_orders_per_customer,
    sum(customer_gmv_brl)                                     as gmv_brl,
    cast(sum(customer_gmv_brl) / count(*) as numeric(14, 2))  as avg_clv_brl
from per_customer
group by cohort_month
