-- Gold/dimension: one row per seller_id. Type 1 (no history kept). Same
-- shape and ZIP-centroid join as dim_customers — sellers and customers are
-- symmetric geographic entities in this model.

with sellers as (

    select * from {{ ref('stg_olist__sellers') }}

),

centroids as (

    select * from {{ ref('int_geolocation__zip_centroids') }}

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['s.seller_id']) }}  as seller_key,

        s.seller_id,
        s.seller_zip_prefix,
        s.seller_city,
        s.seller_state,

        g.latitude   as seller_latitude,
        g.longitude  as seller_longitude

    from sellers s
    left join centroids g on s.seller_zip_prefix = g.zip_prefix

)

select * from final
