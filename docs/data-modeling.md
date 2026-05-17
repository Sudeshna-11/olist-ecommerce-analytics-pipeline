# Data modeling approach

This pipeline uses **medallion layering with a Kimball star schema at the gold layer**, following the modern dbt project structure recommended by dbt Labs.

Medallion and Kimball are not competing choices — medallion describes how data moves through stages of refinement, and Kimball describes how the final business-ready tables are shaped. They compose.

## Layers

| Layer | dbt folder | Schema | Purpose |
|---|---|---|---|
| **Bronze (Raw)** | `models/staging/_sources.yml` | `raw` | 1:1 mirror of source CSVs, untouched |
| **Silver — Staging** | `models/staging/` | `staging` | Rename, cast, light cleaning, 1:1 with sources |
| **Silver — Intermediate** | `models/intermediate/` | `intermediate` | Reusable joins / business logic, never queried directly |
| **Gold — Marts (Star)** | `models/marts/` | `marts` | Kimball facts + dimensions, BI-ready |
| **Gold — Aggregates** | `models/marts/aggregates/` | `marts` | Pre-aggregated tables tuned for dashboards |

## Naming convention (dbt official)

```
<layer>_<source>__<entity>.sql

stg_olist__orders         (staging from olist source)
int_orders__with_payments (intermediate)
fct_order_items           (fact)
dim_customers             (dimension)
mart_daily_revenue        (gold aggregate)
```

## Star schema — gold layer

### Dimensions

| Table | Grain | SCD type | Notes |
|---|---|---|---|
| `dim_customers` | 1 row per customer | Type 1 | ZIP-level geo joined in |
| `dim_products` | 1 row per product | **Type 2** (via dbt snapshot) | English category name joined in; price changes tracked |
| `dim_sellers` | 1 row per seller | Type 1 | ZIP-level geo joined in |
| `dim_dates` | 1 row per calendar day | n/a | Generated with `dbt_utils.date_spine()` |

### Facts

| Table | Grain | Materialization | Notes |
|---|---|---|---|
| `fct_orders` | 1 row per order | table | Header-level — status, totals, delivery times |
| `fct_order_items` | 1 row per order line | **incremental** | Revenue analysis lives here |
| `fct_order_reviews` | 1 row per review | table | 1–5 star reviews |

### Why two facts at different grains?

- `fct_orders` answers: "How many orders shipped on time last month?"
- `fct_order_items` answers: "Which products drove revenue in São Paulo?"

Forcing both questions into one fact would either lose grain (lose product-level detail) or duplicate header columns across line items (wastes storage and risks summation errors). Two facts at their natural grain is the Kimball-correct answer.

## Modeling concepts demonstrated

| Concept | Where |
|---|---|
| **Layered architecture** | staging → intermediate → marts |
| **Naming convention** | `stg_`, `int_`, `fct_`, `dim_`, `mart_` prefixes |
| **Surrogate keys** | `dbt_utils.generate_surrogate_key()` on every dim |
| **Conformed dimensions** | `dim_customers` joined to both fact tables via same key |
| **Grain declaration** | Documented in YAML for every fact |
| **Slowly Changing Dimensions** | Type 2 snapshot on `dim_products` (price history) |
| **Date dimension** | Generated with `dbt_utils.date_spine()` |
| **Source freshness** | `freshness:` block on each source |
| **Data quality tests** | unique, not_null, relationships, accepted_values, custom singular tests |
| **Incremental models** | `fct_order_items` processes only new orders |
| **Macros** | Custom FX-conversion macro (week 2) |
| **dbt docs** | Generated site with lineage graph |

## Why this approach

1. **Recruiter-recognizable:** Medallion is the lakehouse standard (Databricks, Snowflake). Kimball is the classical BI standard. Showing both = depth across modern and traditional stacks.
2. **BI-friendly:** Power BI works beautifully against a star schema — no need for explicit joins in the model.
3. **Maintainable:** Layering means a column rename in raw doesn't ripple through the whole project.
4. **Testable:** Each layer has its own tests, so failures localize.
5. **Documented:** dbt docs renders the full lineage graph automatically.

## What we are **not** doing (and why)

| Approach | Why we skipped it |
|---|---|
| Data Vault 2.0 (Hubs/Links/Sats) | Overkill for portfolio scale; signals "enterprise insurance" not "modern stack" |
| Pure One Big Table (OBT) | Loses dimensional modeling concepts that recruiters look for |
| Pure Snowflake schema (normalized dims) | Storage is cheap; query performance favors denormalized dims |
| 3NF in the warehouse | That's an OLTP pattern; warehouses model for analytics, not transactions |
