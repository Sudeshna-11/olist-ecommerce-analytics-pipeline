-- Gold/dimension: SCD Type 2 product dimension, one row per product
-- *version*, sourced from products_snapshot. English category name joined
-- in from the translation lookup.
--
-- Key discipline for SCD2:
--   * product_key  -> surrogate, unique PER VERSION (includes valid_from),
--                     so it's safe as a fact FK that points at the version
--                     in effect at sale time.
--   * product_id   -> business/natural key, REPEATS across versions — so
--                     it is intentionally NOT unique here.
--   * is_current   -> convenience flag; the open version has valid_to null.
-- The dbt_* bookkeeping columns are renamed to clean valid_from/valid_to so
-- downstream BI never has to know dbt's internals.

with snapshotted as (

    select * from {{ ref('products_snapshot') }}

),

translation as (

    select * from {{ ref('stg_olist__category_translation') }}

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['p.product_id', 'p.dbt_valid_from']) }}  as product_key,

        p.product_id,
        p.product_category_name_pt,
        t.product_category_name_en,

        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,

        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,

        p.dbt_valid_from                                       as valid_from,
        p.dbt_valid_to                                         as valid_to,
        case when p.dbt_valid_to is null then true else false end  as is_current

    from snapshotted p
    left join translation t
        on p.product_category_name_pt = t.product_category_name_pt

)

select * from final
