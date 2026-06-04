# Dashboard design spec

The blueprint for the Power BI report: four pages, each backed by one gold aggregate. This is the layout to build the `.pbix` from — every visual below names its source table, the columns it binds to, and the measure definition it relies on (defined once in **[Metric / KPI spec](metrics.md)**, not repeated here).

Power BI is a GUI and lives outside this repo; what's version-controlled is this spec plus the SQL aggregates it consumes. The `.pbix` and screenshots land in `dashboards/` when built.

## How Power BI consumes the marts

The report connects to the **`ANALYTICS_marts` schema on Snowflake** (prod — the schema is bare `marts` on local Postgres dev) and imports the four aggregate tables, all materialized and tested green on Snowflake:

| Page | Source table | Grain | Connector |
|---|---|---|---|
| Executive Overview | `mart_daily_revenue` | one day | Snowflake (Import mode) |
| Regional Performance | `mart_state_performance` | one state | Snowflake (Import mode) |
| Category Mix | `mart_category_revenue` | one category | Snowflake (Import mode) |
| Seller Scorecard | `mart_seller_performance` | one seller | Snowflake (Import mode) |

**Why four independent tables instead of the raw star.** Each aggregate is a pre-shaped, single-grain rollup — Power BI does no joins, no fan-out, no DAX gymnastics to get a correct number. The tradeoff: the four tables don't cross-filter each other (a state click won't filter the category page). That's deliberate — these are *four standalone executive views*, not one drill-everywhere model. If cross-filtering is wanted later, import the star (`fct_*` + `dim_*`) into a second model; this report is the fast, correct, dashboard-tuned path. **Import mode** (not DirectQuery) because the aggregates are tiny (≤3,095 rows) and refresh nightly — no reason to round-trip Snowflake on every click.

## Global conventions

- **Currency.** BRL is the default and only fully-reconcilable currency. Show `_brl` measures everywhere; expose `_usd` as a secondary KPI on Executive and Category only (where the column exists). Do **not** build a BRL/USD/EUR toggle that swaps a single visual's measure — the USD columns convert goods-only, so a toggled "revenue" would silently change definition (see metrics.md ¹). Keep currency explicit in the column title instead.
- **Ratios are pre-computed or re-derived, never averaged.** `on_time_pct` and `avg_review_score` come straight from the aggregate at its native grain. If a visual rolls them up (e.g. region group), re-derive from components (`sum(n_on_time)/sum(n_delivered)`) via a DAX measure — never `AVERAGE()` the percentage column.
- **Theme.** Match the medallion palette already in the README mermaid diagram — gold (`#1b5e20`) for revenue accents, blue (`#0d3b66`) for the BI/headline band. One accent color per page.
- **Date range.** Data spans **2016-09 → 2018-10** (Olist's real window). Pin the default slicer to the full range; the sparse 2016 tail is real, not a gap — annotate it rather than hiding it.

---

## Page 1 — Executive Overview

**Source:** `mart_daily_revenue` · **Question:** "How is the business trending over time?"

| Slot | Visual | Binding |
|---|---|---|
| KPI card | GMV (BRL) | `sum(gmv_brl)` |
| KPI card | Orders | `sum(n_orders)` |
| KPI card | Items | `sum(n_items)` |
| KPI card | Avg order value | `sum(gmv_brl) / sum(n_orders)` (DAX) |
| Hero | **Line chart** — GMV over time | axis `date_day`, value `sum(gmv_brl)`; secondary line `sum(items_usd)` for the USD view |
| Secondary | **Clustered column** — GMV by month | axis `month_name` (sort by `month`), value `sum(gmv_brl)` |
| Secondary | **Column** — weekday vs weekend split | axis `is_weekend`, value `sum(gmv_brl)` and `sum(n_orders)` |
| Slicers | `year`, `quarter`, `is_weekend` | |

**Notes.** `freight_brl = gmv_brl − items_brl` — optionally show freight as a stacked component of the GMV column to make the goods/shipping split visible. Calendar attributes (`year`/`quarter`/`month`/`is_weekend`) are carried on the aggregate, so no separate date dimension import is needed for this page.

---

## Page 2 — Regional Performance

**Source:** `mart_state_performance` · **Question:** "Where are sales concentrated, and where is delivery weakest?"

| Slot | Visual | Binding |
|---|---|---|
| Hero | **Filled map** of Brazil | location `state` (2-letter UF), color saturation `sum(gmv_brl)` |
| KPI card | Total orders | `sum(n_orders)` |
| KPI card | Avg delivery days (national) | weight by **delivered** orders: `sum(avg_delivery_days * n_delivered) / sum(n_delivered)` — **do not** plain-average (DAX in powerbi-connection.md) |
| KPI card | National on-time % | `sum(n_on_time) / sum(n_delivered)` (DAX) — **not** `AVERAGE(on_time_pct)` |
| Table | State leaderboard | `state`, `n_orders`, `gmv_brl`, `avg_delivery_days`, `on_time_pct`; conditional-format on-time % red→green |
| Secondary | **Scatter** — delivery vs on-time | x `avg_delivery_days`, y `on_time_pct`, size `n_orders`, point `state` — surfaces slow *and* unreliable states |
| Slicers | `state` | |

**Notes.** `on_time_pct` is over **delivered orders only**; `n_delivered` / `n_on_time` are exposed precisely so the national rollup re-derives correctly. SP dominates volume (~40% of Olist orders) — consider a log color scale or a "exclude SP" toggle so the rest of the map isn't washed out.

---

## Page 3 — Category Mix

**Source:** `mart_category_revenue` · **Question:** "Which product categories drive revenue?"

| Slot | Visual | Binding |
|---|---|---|
| Hero | **Bar chart** — top 15 categories by revenue | axis `category`, value `sum(revenue_brl)`, Top-N filter = 15 |
| KPI card | Categories tracked | `distinctcount(category)` (72, incl. `unknown`) |
| KPI card | Revenue in top 15 | share-of-total DAX measure |
| Secondary | **Treemap** — revenue share | group `category`, value `revenue_brl` |
| Secondary | **Scatter** — breadth vs value | x `n_products`, y `revenue_brl`, size `n_orders` — wide-but-thin vs narrow-but-rich categories |
| Table | Category detail | `category`, `n_orders`, `n_items`, `n_products`, `revenue_brl`, `revenue_usd` |
| Slicers | `category` (search-enabled) | |

**Notes.** A multi-category order counts in **each** category, so `sum(n_orders)` across this page **over-counts** vs the true order total — label the order count "category-orders" or footnote it; use Page 1 / Page 2 for a true order count. `unknown` (products with no category) is a real bucket, not a null — keep it visible. `revenue_brl` includes freight; `revenue_usd` is goods-only — don't present them as the same measure in two currencies.

---

## Page 4 — Seller Scorecard

**Source:** `mart_seller_performance` · **Question:** "Who are the top and bottom sellers, by revenue and by rating?"

| Slot | Visual | Binding |
|---|---|---|
| KPI card | Active sellers | `distinctcount(seller_key)` (3,095) |
| KPI card | Avg rating (volume-weighted) | `sum(avg_review_score * n_reviews) / sum(n_reviews)` (DAX) — **not** `AVERAGE(avg_review_score)` |
| Hero | **Table / matrix** — seller leaderboard | `seller_id`, `seller_state`, `seller_city`, `n_orders`, `revenue_brl`, `avg_review_score`, `n_reviews`; sort by revenue, star-rating data bars |
| Secondary | **Scatter** — revenue vs rating | x `avg_review_score`, y `revenue_brl`, size `n_orders` — finds high-revenue/low-rating sellers (churn risk) |
| Secondary | **Column** — sellers by state | axis `seller_state`, value `distinctcount(seller_key)` |
| Slicers | `seller_state`, `avg_review_score` band | |

**Notes.** Sellers with no reviews show `avg_review_score = (blank)` / `n_reviews = 0` — filter them out of rating visuals but keep them in revenue visuals. A review on a multi-seller order is attributed to **both** sellers, so the volume-weighted national average isn't a pure customer-level mean — acceptable for a seller scorecard (documented in metrics.md).

---

## Cross-page slicers & interactions

- A **date slicer** only applies to Page 1 (the only time-grained aggregate). The other three are point-in-time rollups over the full history — don't fake a date filter on them.
- Set **edit-interactions** so KPI cards don't get filtered by their own page's detail table clicks where that would double-filter.
- Add a **report-level tooltip page** showing the underlying counts (`n_orders`, `n_items`) so any revenue figure can be sanity-checked on hover.

## What's intentionally omitted

| Not shown | Why |
|---|---|
| Customer retention page | `mart_customer_cohorts` now **exists** (acquisition-month grain, repeat-rate + CLV via `customer_unique_id`) but its dashboard page isn't laid out here yet — a candidate 5th page. Measures are in [metrics.md](metrics.md). |
| EUR revenue | Only `mart_daily_revenue` carries `items_eur`; not enough coverage for a dedicated visual. |
| Payment-method breakdown | Lives on `fct_orders`, not surfaced in any aggregate — add a `mart_payment_mix` if a dashboard needs it. |
| Live/DirectQuery refresh | Aggregates are tiny and refresh nightly; Import mode is correct. |
