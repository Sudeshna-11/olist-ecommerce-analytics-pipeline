-- Singular test: the core SCD2 invariant. Every product_id must have
-- exactly one currently-effective version (is_current = true). If a
-- snapshot run ever left two open versions for one product (valid_to null
-- on both), this query returns those product_ids and the test fails.
-- A passing test returns zero rows.

select
    product_id,
    count(*) as current_versions
from {{ ref('dim_products') }}
where is_current
group by product_id
having count(*) > 1
