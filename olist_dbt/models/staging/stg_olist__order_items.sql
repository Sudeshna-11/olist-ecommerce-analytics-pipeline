-- Silver: order line items. Composite PK = (order_id, order_item_id).
-- Each order has 1..N items; order_item_id is a 1-based sequence inside
-- the order, not a globally unique id. Drives every revenue / item-count
-- metric downstream.

with source as (

    select * from {{ source('olist_raw', 'raw_order_items') }}

),

renamed as (

    select
        cast(order_id as varchar)               as order_id,
        cast(order_item_id as integer)          as order_item_seq,
        cast(product_id as varchar)             as product_id,
        cast(seller_id as varchar)              as seller_id,
        cast(shipping_limit_date as timestamp)  as shipping_limit_at,
        cast(price as numeric(12, 2))           as item_price_brl,
        cast(freight_value as numeric(12, 2))   as freight_brl
    from source

)

select * from renamed
