-- Silver/intermediate: collapse the ~1M-row geolocation table to one
-- representative (lat, lng) per zip_prefix. Both dim_customers and
-- dim_sellers want a single coordinate per ZIP, so this is the shared
-- input. Ephemeral, consistent with the layer convention — Postgres
-- aggregates the 1M rows in well under a second, so re-inlining it in two
-- dims is cheap enough not to warrant materialising a relation.
--
-- Data quality: the raw geolocation has a small number of corrupt points
-- (coordinates in other hemispheres / continents). Averaging them in would
-- drag a ZIP's centroid off the map, so we clip to Brazil's bounding box
-- before averaging. Bounds are generous: lat -34..6, lng -74..-34.

with geo as (

    select * from {{ ref('stg_olist__geolocation') }}

),

cleaned as (

    select *
    from geo
    where latitude  between -34.0 and 6.0
      and longitude between -74.0 and -34.0

),

centroids as (

    select
        zip_prefix,
        avg(latitude)   as latitude,
        avg(longitude)  as longitude,
        count(*)        as n_points
    from cleaned
    group by zip_prefix

)

select * from centroids
