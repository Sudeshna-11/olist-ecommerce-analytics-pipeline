-- Silver: customers, lightly cleaned. One row per customer_id.
--   * customer_id        -> per-order identity (a returning shopper has a NEW one each order)
--   * customer_unique_id -> stable identity across orders (use this to count repeat customers)
-- Normalisation: city to lowercase (raw data is inconsistent), state to upper.

with source as (

    select * from {{ source('olist_raw', 'raw_customers') }}

),

renamed as (

    select
        cast(customer_id as varchar)                  as customer_id,
        cast(customer_unique_id as varchar)           as customer_unique_id,
        cast(customer_zip_code_prefix as varchar)     as customer_zip_prefix,
        lower(cast(customer_city as varchar))         as customer_city,
        upper(cast(customer_state as varchar))        as customer_state
    from source

)

select * from renamed
