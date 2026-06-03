-- Gold/dimension: one row per calendar day. Generated, not loaded — a
-- calendar is fully derivable, so dbt_utils.date_spine() gives us a clean,
-- deterministic dim with no ingest step.
--
-- Range: 2016-01-01 .. 2018-12-31. The Olist orders run late-2016 ..
-- late-2018 and the FX rates 2016-09-01 .. 2018-12-31, so this comfortably
-- covers every fact date. date_spine's end_date is EXCLUSIVE, hence
-- 2019-01-01 below.
--
-- date_key (YYYYMMDD integer) is the surrogate the facts join on; date_day
-- is the human-readable natural key. Month/day names are built with case
-- expressions rather than to_char() so the model is portable across
-- Postgres and Snowflake. day_of_week uses extract(dow): 0=Sunday..6=Sat
-- on Postgres — on Snowflake this depends on the WEEK_START session param
-- (default also Sunday=0), revisited if/when prod diverges.

with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2019-01-01' as date)"
    ) }}

),

final as (

    select
        cast(date_day as date)                                       as date_day,

        cast(extract(year  from date_day) * 10000
             + extract(month from date_day) * 100
             + extract(day   from date_day) as integer)              as date_key,

        cast(extract(year    from date_day) as integer)              as year,
        cast(extract(quarter from date_day) as integer)              as quarter,
        cast(extract(month   from date_day) as integer)              as month,
        cast(extract(day     from date_day) as integer)              as day_of_month,
        cast(extract(doy     from date_day) as integer)              as day_of_year,
        cast(extract(week    from date_day) as integer)              as week_of_year,
        cast(extract(dow     from date_day) as integer)              as day_of_week,

        case extract(month from date_day)
            when 1 then 'January'   when 2 then 'February' when 3 then 'March'
            when 4 then 'April'     when 5 then 'May'      when 6 then 'June'
            when 7 then 'July'      when 8 then 'August'   when 9 then 'September'
            when 10 then 'October'  when 11 then 'November' when 12 then 'December'
        end                                                          as month_name,

        case extract(dow from date_day)
            when 0 then 'Sunday'    when 1 then 'Monday'   when 2 then 'Tuesday'
            when 3 then 'Wednesday' when 4 then 'Thursday' when 5 then 'Friday'
            when 6 then 'Saturday'
        end                                                          as day_name,

        case when extract(dow from date_day) in (0, 6)
             then true else false end                                as is_weekend

    from spine

)

select * from final
