-- Silver: orders, with timestamps cast and a couple of derived booleans.
-- One row per order_id. Five timestamp columns (purchase, approved,
-- carrier-hand-off, customer-delivery, estimated-delivery) drive every
-- downstream delivery-SLA metric in the marts layer.

with source as (

    select * from {{ source('olist_raw', 'raw_orders') }}

),

renamed as (

    select
        cast(order_id as varchar)                            as order_id,
        cast(customer_id as varchar)                         as customer_id,
        cast(order_status as varchar)                        as order_status,

        cast(order_purchase_timestamp as timestamp)          as purchased_at,
        cast(order_approved_at as timestamp)                 as approved_at,
        cast(order_delivered_carrier_date as timestamp)      as delivered_to_carrier_at,
        cast(order_delivered_customer_date as timestamp)     as delivered_to_customer_at,
        cast(order_estimated_delivery_date as timestamp)     as estimated_delivery_at,

        -- Derived flags used a lot downstream; cheap to compute once here
        case when order_status = 'delivered' then true else false end                                as is_delivered,
        case when cast(order_delivered_customer_date as timestamp)
                  > cast(order_estimated_delivery_date as timestamp) then true else false end       as is_late

    from source

)

select * from renamed
