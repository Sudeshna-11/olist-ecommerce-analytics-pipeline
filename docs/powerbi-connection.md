# Power BI — connection & DAX guide

How to wire Power BI Desktop to the Snowflake `ANALYTICS_marts` schema, shape the four aggregates, and the complete DAX measure set the dashboard ([dashboards.md](dashboards.md)) is built on. Measure *definitions* live in [metrics.md](metrics.md); this doc is the implementation.

## Prerequisites

- **Power BI Desktop** (Windows) — the Snowflake connector ships built-in, no driver install.
- A **Snowflake login** with read access to `OLIST.ANALYTICS_marts`. Use a read-only role for BI (see [Security](#security) — don't reuse the `ACCOUNTADMIN` role dbt runs under).
- The four aggregates materialized on prod — already done: `dbt build --target prod --select path:models/marts/aggregates` (18/18 green).

## Connection parameters

These mirror `olist_dbt/profiles.yml` (prod target). The dbt `schema: ANALYTICS` becomes **`ANALYTICS_marts`** because the marts models set a `marts` custom schema suffix.

| Field | Value | Source |
|---|---|---|
| Server | `<account>.snowflakecomputing.com` | `SNOWFLAKE_ACCOUNT` in `.secrets.env` |
| Warehouse | `COMPUTE_WH` | `SNOWFLAKE_WAREHOUSE` (profile default) |
| Database | `OLIST` | `SNOWFLAKE_DATABASE` (profile default) |
| Schema | `ANALYTICS_marts` | `ANALYTICS` base + `marts` suffix |
| Role | a read-only BI role (see below) | — |

> The account locator (the `<account>` part) is the string before `.snowflakecomputing.com` in your Snowflake URL — e.g. `ab12345.eu-west-1`. It's not a secret, but it's per-account, so it's not committed here.

## Step 1 — Connect (Import mode)

1. **Home → Get Data → Snowflake.**
2. Server = `<account>.snowflakecomputing.com`, Warehouse = `COMPUTE_WH`.
3. Data Connectivity mode = **Import** (not DirectQuery). The aggregates are ≤3,095 rows and refresh nightly — there's no reason to round-trip Snowflake on every click, and Import gives the snappiest report.
4. Authenticate (Snowflake username/password, or SSO if your account uses it).
5. In the Navigator, expand `OLIST → ANALYTICS_marts` and tick the five tables:
   - `MART_DAILY_REVENUE`
   - `MART_CATEGORY_REVENUE`
   - `MART_STATE_PERFORMANCE`
   - `MART_SELLER_PERFORMANCE`
   - `MART_CUSTOMER_COHORTS`
6. **Load** (not Transform, unless you want the optional renames in Step 2).

Snowflake returns identifiers **uppercased** (`GMV_BRL`, `MART_DAILY_REVENUE`). DAX is case-insensitive, so the measures below resolve whether you leave them uppercase or rename — no need to touch them.

## Step 2 — Data types & formatting (optional but recommended)

In **Transform Data** (Power Query) or the column tools, set:

| Column pattern | Type / format |
|---|---|
| `*_brl`, `*_usd`, `*_eur`, `gmv_*`, `revenue_*` | Fixed decimal → currency, 2 dp |
| `date_day` | Date |
| `date_key`, `purchase_date_key` | Whole number (it's a YYYYMMDD surrogate — mark **Do not summarize**) |
| `n_*` (counts) | Whole number, **Do not summarize** |
| `avg_review_score`, `avg_delivery_days`, `on_time_pct`, `repeat_rate_pct`, `avg_orders_per_customer`, `avg_clv_brl` | Decimal, **Do not summarize** (these are pre-computed ratios/averages — never let Power BI auto-sum them) |
| `cohort_month` | Date |

Marking the count and ratio columns "Do not summarize" is the single most important step: it stops a careless drag-to-canvas from silently summing `on_time_pct` or averaging `n_orders`.

## Step 3 — The data model (no relationships)

Leave the five tables **unrelated**. Each is a standalone single-grain rollup feeding its own page; there's no conformed key to join them on at this grain, and faking one would let one page silently mis-filter another. This is the deliberate trade from [dashboards.md](dashboards.md#how-power-bi-consumes-the-marts) — five correct standalone views over one cross-filtering model.

Create one empty **`_Measures`** table (Home → Enter Data → blank table named `_Measures`) and house every measure below in it, so measures are organized by intent rather than scattered across the four source tables.

## DAX measures

Paste these into the `_Measures` table. Table/column names are the warehouse names; DAX resolves them case-insensitively.

### Executive Overview — `mart_daily_revenue`

```dax
GMV (BRL)            = SUM(mart_daily_revenue[gmv_brl])
Merch Revenue (BRL)  = SUM(mart_daily_revenue[items_brl])
Merch Revenue (USD)  = SUM(mart_daily_revenue[items_usd])
Freight (BRL)        = SUM(mart_daily_revenue[freight_brl])
Orders               = SUM(mart_daily_revenue[n_orders])
Items                = SUM(mart_daily_revenue[n_items])
Avg Order Value (BRL) = DIVIDE([GMV (BRL)], [Orders])
```

`n_sellers` is a **per-day** distinct count — it is *not* additive across days (a seller active on two days is counted twice). Don't build a "total active sellers" card from this table; use `Active Sellers` from the seller table for a true count. Show `n_sellers` only inside a single-day context.

### Regional Performance — `mart_state_performance`

```dax
State Orders      = SUM(mart_state_performance[n_orders])
State GMV (BRL)   = SUM(mart_state_performance[gmv_brl])
Delivered Orders  = SUM(mart_state_performance[n_delivered])
On-Time Orders    = SUM(mart_state_performance[n_on_time])

On-Time %         = DIVIDE([On-Time Orders], [Delivered Orders])

Avg Delivery Days =
    DIVIDE(
        SUMX(
            mart_state_performance,
            mart_state_performance[avg_delivery_days] * mart_state_performance[n_delivered]
        ),
        [Delivered Orders]
    )
```

Both `On-Time %` and `Avg Delivery Days` **re-derive from component counts** so they roll up correctly across states — never `AVERAGE([on_time_pct])` or `AVERAGE([avg_delivery_days])`. The delivery average is weighted by `n_delivered` (not `n_orders`), because the per-state `avg_delivery_days` is computed over *delivered* orders only — non-delivered orders have no delivery date to average. Format `On-Time %` as a percentage (the stored value is already 0–100, so set format to a plain number with a `%` suffix, or divide by 100 if you prefer a true percentage type).

### Category Mix — `mart_category_revenue`

```dax
Category Revenue (BRL) = SUM(mart_category_revenue[revenue_brl])
Category Revenue (USD) = SUM(mart_category_revenue[revenue_usd])
Category Items         = SUM(mart_category_revenue[n_items])
Category Products      = SUM(mart_category_revenue[n_products])
Categories Tracked     = DISTINCTCOUNT(mart_category_revenue[category])

Category Orders        = SUM(mart_category_revenue[n_orders])   -- see caveat

Revenue % of Total =
    DIVIDE(
        [Category Revenue (BRL)],
        CALCULATE([Category Revenue (BRL)], REMOVEFILTERS(mart_category_revenue))
    )
```

`Category Orders` **over-counts**: a multi-category order is counted in each of its categories, so this won't reconcile to the true order total — label it "category-orders" in visuals and use `Orders` (daily) or `State Orders` for a real total. `Category Products` is safe to sum (a product belongs to exactly one category). `Category Revenue (BRL)` includes freight; `Category Revenue (USD)` is goods-only — keep their titles explicit, they are not the same measure at an FX rate (see metrics.md ¹).

### Seller Scorecard — `mart_seller_performance`

```dax
Active Sellers       = DISTINCTCOUNT(mart_seller_performance[seller_key])
Seller Revenue (BRL) = SUM(mart_seller_performance[revenue_brl])
Seller Revenue (USD) = SUM(mart_seller_performance[revenue_usd])
Total Reviews        = SUM(mart_seller_performance[n_reviews])

Seller Orders        = SUM(mart_seller_performance[n_orders])   -- over-counts multi-seller orders

Avg Review Score =
    DIVIDE(
        SUMX(
            mart_seller_performance,
            mart_seller_performance[avg_review_score] * mart_seller_performance[n_reviews]
        ),
        [Total Reviews]
    )
```

`Avg Review Score` is **volume-weighted** by `n_reviews` so it rolls up correctly — never `AVERAGE([avg_review_score])`, which would weight a 1-review seller the same as a 1,000-review seller. Sellers with `n_reviews = 0` carry a blank `avg_review_score`; they contribute 0 to both sides of the DIVIDE, so they drop out of the weighted average cleanly while still counting in revenue measures. `Seller Orders` over-counts multi-seller orders — same caveat as category.

### Customer Retention — `mart_customer_cohorts`

```dax
Total Customers      = SUM(mart_customer_cohorts[n_customers])
Repeat Customers     = SUM(mart_customer_cohorts[n_repeat_customers])
Total Customer Orders = SUM(mart_customer_cohorts[total_orders])
Lifetime GMV (BRL)   = SUM(mart_customer_cohorts[gmv_brl])

Repeat Rate %        = DIVIDE([Repeat Customers], [Total Customers])
Orders per Customer  = DIVIDE([Total Customer Orders], [Total Customers])
Avg CLV (BRL)        = DIVIDE([Lifetime GMV (BRL)], [Total Customers])
```

Every ratio here **re-derives from `n_customers`**, so it's correct at any grain — a single cohort, a slicer range, or the grand total. The three stored ratio columns (`repeat_rate_pct`, `avg_orders_per_customer`, `avg_clv_brl`) are valid **only** in a single-cohort row context; the moment a card or a multi-cohort visual aggregates them, use these measures. `AVERAGE([repeat_rate_pct])` would weight a 200-customer cohort the same as a 12,000-customer one and report a wrong national rate (the un-weighted mean of monthly rates ≠ the true 3.1%). Because customers are keyed by `customer_unique_id`, `Total Customers` is a genuine unique-shopper count (96,096) — the only "count" in the whole model that's safe to read as a deduplicated total.

## Refresh strategy

- **Import + scheduled refresh.** Point a refresh at ~07:00, after the nightly dbt run lands fresh aggregates. Publishing to the Power BI Service + a scheduled refresh needs Snowflake credentials stored in the dataset settings (or an on-premises/VNet gateway if the account isn't reachable from the Service).
- The aggregates are tiny, so a full refresh is seconds — no incremental-refresh policy needed.

## Security

Don't connect Power BI with the `ACCOUNTADMIN` role dbt uses to build. Create a read-only role scoped to the marts:

```sql
CREATE ROLE IF NOT EXISTS PBI_READER;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE PBI_READER;
GRANT USAGE ON DATABASE OLIST TO ROLE PBI_READER;
GRANT USAGE ON SCHEMA OLIST.ANALYTICS_marts TO ROLE PBI_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA OLIST.ANALYTICS_marts TO ROLE PBI_READER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA OLIST.ANALYTICS_marts TO ROLE PBI_READER;
GRANT ROLE PBI_READER TO USER <your_bi_user>;
```

Then select `PBI_READER` as the role in the Snowflake connection. BI tools should read marts, never hold build privileges.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Schema `ANALYTICS_marts` not in Navigator | Marts not built on prod, or wrong role. Run the prod aggregate build; confirm the role has `USAGE` on the schema. |
| `on_time_pct` shows as a giant sum | Column wasn't set "Do not summarize" — fix in Step 2, or always use the `On-Time %` measure, never the raw column. |
| Numbers differ from Postgres dev | Expected only if prod data differs; the SQL is identical across backends. Re-run `dbt build --target prod` to refresh. |
| Map shows only SP/RJ | SP dominates volume — apply a log color scale or an "exclude SP" toggle (noted in dashboards.md). |
