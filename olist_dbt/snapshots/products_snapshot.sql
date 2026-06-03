{% snapshot products_snapshot %}

-- SCD Type 2 source for dim_products. Captures the product catalogue's
-- descriptive attributes over time. The Olist dump is static, so the first
-- run records one version per product; the machinery is what matters —
-- were a product re-categorised or re-measured, dbt would close the old
-- row (dbt_valid_to) and open a new one on the next snapshot.
--
-- strategy='check' (not 'timestamp'): the products source has no reliable
-- updated_at column, so we let dbt diff the listed check_cols to detect a
-- change. We deliberately do NOT track the *_length columns — those are
-- artefacts of the raw export (title/description char counts), not real
-- product attributes, so changes in them shouldn't spawn a new version.

{{
    config(
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=[
            'product_category_name_pt',
            'product_weight_g',
            'product_length_cm',
            'product_height_cm',
            'product_width_cm',
            'product_photos_qty'
        ]
    )
}}

select
    product_id,
    product_category_name_pt,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from {{ ref('stg_olist__products') }}

{% endsnapshot %}
