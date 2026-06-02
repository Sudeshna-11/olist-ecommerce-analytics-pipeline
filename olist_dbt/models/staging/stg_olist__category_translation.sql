-- Silver: Portuguese -> English category lookup. PK = product_category_name_pt.
-- 71 rows. Joined onto stg_olist__products at the intermediate layer.

with source as (

    select * from {{ source('olist_raw', 'raw_category_translation') }}

),

renamed as (

    select
        cast(product_category_name as varchar)          as product_category_name_pt,
        cast(product_category_name_english as varchar)  as product_category_name_en
    from source

)

select * from renamed
