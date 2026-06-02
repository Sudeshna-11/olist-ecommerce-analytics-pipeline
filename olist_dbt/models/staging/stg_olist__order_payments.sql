-- Silver: order payments. Composite PK = (order_id, payment_sequential).
-- An order can be paid in multiple installments and/or split across
-- payment methods; payment_sequential numbers the splits 1..N.
-- payment_installments is the credit-card installment plan length.

with source as (

    select * from {{ source('olist_raw', 'raw_order_payments') }}

),

renamed as (

    select
        cast(order_id as varchar)                as order_id,
        cast(payment_sequential as integer)      as payment_seq,
        cast(payment_type as varchar)            as payment_type,
        cast(payment_installments as integer)    as payment_installments,
        cast(payment_value as numeric(12, 2))    as payment_brl
    from source

)

select * from renamed
