-- Gold/dimension: one row per customer_id. Type 1 (no history kept —
-- customer attributes are static in this dataset). ZIP-level geo centroid
-- joined in so the dim carries a plottable coordinate.
--
-- Note the two identities (carried from staging): customer_id is the
-- per-order identity (the grain here), customer_unique_id is the stable
-- cross-order shopper identity used to count repeat buyers.
--
-- customer_key is the surrogate the facts should eventually join on; we
-- keep customer_id too (fct_orders currently joins on it) until facts are
-- switched over to the surrogate.

with customers as (

    select * from {{ ref('stg_olist__customers') }}

),

centroids as (

    select * from {{ ref('int_geolocation__zip_centroids') }}

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['c.customer_id']) }}  as customer_key,

        c.customer_id,
        c.customer_unique_id,
        c.customer_zip_prefix,
        c.customer_city,
        c.customer_state,

        g.latitude   as customer_latitude,
        g.longitude  as customer_longitude

    from customers c
    left join centroids g on c.customer_zip_prefix = g.zip_prefix

)

select * from final
