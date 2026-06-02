-- Silver: product catalog. PK = product_id.
-- The raw CSV has misspelled "lenght" columns — corrected here as a
-- legitimate cleanup. Category is Portuguese; the English label is
-- joined in at the intermediate layer via stg_olist__category_translation.
-- A small number of products have null category_name (and matching null
-- dimensions) — kept as-is at staging, handled downstream.

with source as (

    select * from {{ source('olist_raw', 'raw_products') }}

),

renamed as (

    select
        cast(product_id as varchar)                  as product_id,
        cast(product_category_name as varchar)       as product_category_name_pt,

        cast(product_name_lenght as integer)         as product_name_length,
        cast(product_description_lenght as integer)  as product_description_length,
        cast(product_photos_qty as integer)          as product_photos_qty,

        cast(product_weight_g as integer)            as product_weight_g,
        cast(product_length_cm as integer)           as product_length_cm,
        cast(product_height_cm as integer)           as product_height_cm,
        cast(product_width_cm as integer)            as product_width_cm
    from source

)

select * from renamed
