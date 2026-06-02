-- Silver: sellers. PK = seller_id.
-- Same zip / city / state normalisation as customers.

with source as (

    select * from {{ source('olist_raw', 'raw_sellers') }}

),

renamed as (

    select
        cast(seller_id as varchar)                  as seller_id,
        cast(seller_zip_code_prefix as varchar)     as seller_zip_prefix,
        lower(cast(seller_city as varchar))         as seller_city,
        upper(cast(seller_state as varchar))        as seller_state
    from source

)

select * from renamed
