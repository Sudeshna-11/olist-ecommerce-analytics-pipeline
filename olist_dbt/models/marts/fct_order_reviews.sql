-- Gold/fact: one row per (review_id, order_id) review. Grain chosen after
-- profiling the source: review_id alone is NOT unique (814 rows come from
-- reviews that cover more than one order) and order_id alone is NOT unique
-- (551 orders carry more than one review) — but the (review_id, order_id)
-- PAIR is unique (0 dupes). So the pair is the grain and the surrogate
-- review_key is built from it. review_id / order_id are kept as their own
-- columns but are intentionally non-unique here.
--
-- review_score is the measure. response time (form sent -> customer answered)
-- is derived. Two date FKs: when the review was created, and when the order
-- was purchased — both conformed to dim_dates. customer_key reaches the
-- shopper via the order.

with reviews as (

    select * from {{ ref('stg_olist__order_reviews') }}

),

orders as (

    select order_id, customer_id, purchased_at
    from {{ ref('stg_olist__orders') }}

),

joined as (

    select
        r.review_id,
        r.order_id,
        o.customer_id,

        r.review_score,
        r.has_review_text,
        r.review_created_at,
        r.review_answered_at,
        o.purchased_at

    from reviews r
    left join orders o on r.order_id = o.order_id

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['j.review_id', 'j.order_id']) }}  as review_key,

        j.review_id,
        j.order_id,
        c.customer_key,

        cast(extract(year  from j.review_created_at) * 10000
             + extract(month from j.review_created_at) * 100
             + extract(day   from j.review_created_at) as integer)   as review_date_key,
        cast(extract(year  from j.purchased_at) * 10000
             + extract(month from j.purchased_at) * 100
             + extract(day   from j.purchased_at) as integer)        as purchase_date_key,

        j.review_score,
        j.has_review_text,

        j.review_created_at,
        j.review_answered_at,
        {{ dbt.datediff('j.review_created_at', 'j.review_answered_at', 'day') }}  as review_response_days

    from joined j
    left join {{ ref('dim_customers') }} c on j.customer_id = c.customer_id

)

select * from final
