-- Silver: zip -> lat/lng map. NOT unique on zip_prefix (multiple
-- coordinates per prefix). Aggregation to one centroid per prefix
-- belongs in the intermediate layer (int_geolocation__zip_centroids),
-- so staging just renames and normalises.

with source as (

    select * from {{ source('olist_raw', 'raw_geolocation') }}

),

renamed as (

    select
        cast(geolocation_zip_code_prefix as varchar)  as zip_prefix,
        cast(geolocation_lat as double precision)     as latitude,
        cast(geolocation_lng as double precision)     as longitude,
        lower(cast(geolocation_city as varchar))      as city,
        upper(cast(geolocation_state as varchar))     as state
    from source

)

select * from renamed
