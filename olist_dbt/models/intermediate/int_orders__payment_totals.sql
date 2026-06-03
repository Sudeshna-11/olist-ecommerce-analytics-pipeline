-- Silver/intermediate: collapse the (order_id, payment_seq) payment grain
-- down to one row per order_id. An order can be split across multiple
-- payment methods and/or installment plans; here we sum the value and
-- summarise the splits. Ephemeral, same as int_orders__item_totals.
--
-- max_installments is the longest credit-card plan on the order (boleto /
-- voucher rows carry installments = 1). Left null-safe downstream because
-- a handful of orders have no payment row at all.

with payments as (

    select * from {{ ref('stg_olist__order_payments') }}

),

aggregated as (

    select
        order_id,
        count(*)                       as n_payment_records,
        count(distinct payment_type)   as n_payment_types,
        max(payment_installments)      as max_installments,
        sum(payment_brl)               as total_payment_brl
    from payments
    group by order_id

)

select * from aggregated
