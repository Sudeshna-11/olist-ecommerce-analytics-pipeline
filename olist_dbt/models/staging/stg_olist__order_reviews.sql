-- Silver: post-purchase reviews. PK = review_id (mostly).
-- KNOWN OLIST QUIRK: a tiny fraction of review_ids appear on more than
-- one order (the same review covered multiple deliveries). We keep both
-- rows in staging and let downstream collapse if needed — the unique
-- test on review_id is set to severity=warn in _schema.yml.

with source as (

    select * from {{ source('olist_raw', 'raw_order_reviews') }}

),

renamed as (

    select
        cast(review_id as varchar)                  as review_id,
        cast(order_id as varchar)                   as order_id,
        cast(review_score as integer)               as review_score,
        cast(review_comment_title as varchar)       as review_title,
        cast(review_comment_message as varchar)     as review_message,
        cast(review_creation_date as timestamp)     as review_created_at,
        cast(review_answer_timestamp as timestamp)  as review_answered_at,

        case when review_comment_message is not null
                  and length(trim(cast(review_comment_message as varchar))) > 0
             then true else false end               as has_review_text
    from source

)

select * from renamed
