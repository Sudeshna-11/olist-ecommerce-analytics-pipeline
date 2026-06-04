# Metric / KPI specification

The single source of truth for **what each dashboard number means and where it comes from**. Every KPI below is defined once here, then mapped to the five gold aggregates that expose it. If a measure looks the same in two tiles but is computed differently, this doc is where that gets caught.

The five aggregates (`models/marts/aggregates/`) are single-grain rollups over the star schema:

| Aggregate | Grain (one row per…) | Built from | Dashboard view |
|---|---|---|---|
| `mart_daily_revenue` | calendar day | `fct_order_items` + `dim_dates` | Executive time series |
| `mart_category_revenue` | product category | `fct_order_items` + `dim_products` | Category mix |
| `mart_state_performance` | customer state | `fct_orders` + `dim_customers` | Regional map |
| `mart_seller_performance` | seller | `fct_order_items` + `fct_order_reviews` + `dim_sellers` | Seller scorecard |
| `mart_customer_cohorts` | acquisition month | `fct_orders` + `dim_customers` | Customer retention |

## Conventions

- **Currency.** `_brl` is the native amount. `_usd` / `_eur` are derived from the forward-filled daily FX rate (the `convert_brl` macro) and convert the **goods price only** (`item_price_brl`), *not* freight — so foreign-currency columns are merchandise value, not GMV. BRL is the only fully reconcilable currency; treat USD/EUR as indicative.
- **GMV = goods + freight.** Both `gmv_brl` columns (daily, state) and the category/seller `revenue_brl` resolve to *item price + freight*. They agree because `mart_daily_revenue.gmv_brl = sum(item_revenue_brl)` and `mart_state_performance.gmv_brl = sum(gross_merchandise_brl)`, and `gross_merchandise_brl` is itself `sum(item_price) + sum(freight)` per order. One definition, two grains.
- **Additivity.** A measure is *additive* only across the grains noted. `on_time_pct` and `avg_review_score` are **ratios/averages — never sum them**; re-derive from their numerator/denominator components when rolling up.
- **Revenue grain vs. order grain.** Line-item tables (`fct_order_items`) let one order contribute to several categories/sellers. The header table (`fct_orders`) counts each order once. This is why state revenue uses the header fact (no double-count per order) while category/seller revenue uses line items (intentional split across categories/sellers).
- **Customer identity.** Repeat-purchase and CLV are counted over **`customer_unique_id`** (the stable shopper), *not* `customer_id` (which Olist mints fresh per order). Counting `customer_id` would make every shopper look new and the repeat rate collapse to ~0. The cohort mart resolves the unique identity through `dim_customers`.

## Metric catalog

| KPI | Definition | Formula (source) | Currency | Additive across |
|---|---|---|---|---|
| **GMV** | Gross merchandise value: goods + freight | `sum(item_price_brl + freight_brl)` | BRL | day, state |
| **Merchandise revenue** | Goods value, freight excluded | `sum(item_price_brl)` | BRL/USD/EUR | category, seller, day |
| **Freight** | Shipping charged | `sum(freight_brl)` | BRL | day |
| **Orders** | Distinct orders | `count(distinct order_id)` *(line facts)* / `count(*)` *(header)* | — | see note |
| **Items** | Order lines | `count(*)` over `fct_order_items` | — | day, category, seller |
| **Active sellers** | Distinct sellers transacting | `count(distinct seller_key)` | — | day |
| **Products sold** | Distinct products | `count(distinct product_id)` | — | category |
| **Avg delivery days** | Purchase → customer delivery, delivered orders only | `avg(delivery_days)` | days | **no — average** |
| **On-time %** | Delivered on/before estimate, as % of delivered | `100 * n_on_time / n_delivered` | % | **no — ratio** |
| **Avg review score** | Mean 1–5 star score over a seller's orders | `avg(review_score)` | stars | **no — average** |
| **Customers acquired** | Distinct new shoppers in the cohort month | `count(distinct customer_unique_id)` | — | cohort month |
| **Repeat customers** | Of a cohort, those who ever placed a 2nd+ order | `count(*) where lifetime_orders > 1` | — | cohort month |
| **Repeat-purchase rate** | Repeat customers as % of the cohort | `100 * n_repeat_customers / n_customers` | % | **no — ratio** |
| **Orders per customer** | Lifetime orders ÷ customers in the cohort | `avg(lifetime_orders)` | — | **no — average** |
| **CLV (avg)** | Lifetime GMV per customer in the cohort | `sum(customer_gmv) / n_customers` | BRL | **no — average** |

> **Orders additivity caveat.** `count(distinct order_id)` is additive across *days* (an order has one purchase date) but **not** across categories or sellers (a multi-category / multi-seller order is counted in each). Summing `n_orders` across category or seller rows over-counts. Use `mart_state_performance.n_orders` or daily `n_orders` for a true order total.

## Measure → aggregate matrix

Column name each KPI carries in each aggregate (— = not exposed at that grain):

| KPI | `mart_daily_revenue` | `mart_category_revenue` | `mart_state_performance` | `mart_seller_performance` | `mart_customer_cohorts` |
|---|---|---|---|---|---|
| GMV (BRL) | `gmv_brl` | `revenue_brl` ¹ | `gmv_brl` | `revenue_brl` ¹ | `gmv_brl` |
| Merchandise revenue (USD) | `items_usd` | `revenue_usd` | — | `revenue_usd` | — |
| Merchandise revenue (BRL) | `items_brl` | `revenue_brl` ¹ | — | `revenue_brl` ¹ | — |
| Merchandise revenue (EUR) | `items_eur` | — | — | — | — |
| Freight (BRL) | `freight_brl` | — | — | — | — |
| Orders | `n_orders` | `n_orders` | `n_orders` | `n_orders` | `total_orders` |
| Items | `n_items` | `n_items` | — | `n_items` | — |
| Active sellers | `n_sellers` | — | — | — | — |
| Products sold | — | `n_products` | — | — | — |
| Avg delivery days | — | — | `avg_delivery_days` | — | — |
| On-time % | — | — | `on_time_pct` | — | — |
| Delivered count | — | — | `n_delivered` | — | — |
| On-time count | — | — | `n_on_time` | — | — |
| Avg review score | — | — | — | `avg_review_score` | — |
| Reviews | — | — | — | `n_reviews` | — |
| Customers acquired | — | — | — | — | `n_customers` |
| Repeat customers | — | — | — | — | `n_repeat_customers` |
| Repeat-purchase rate | — | — | — | — | `repeat_rate_pct` |
| Orders per customer | — | — | — | — | `avg_orders_per_customer` |
| CLV (avg) | — | — | — | — | `avg_clv_brl` |

¹ **Naming caveat — `revenue_brl` is GMV-grade (goods + freight) in category and seller, but the matching `revenue_usd` converts goods only.** So within `mart_category_revenue` and `mart_seller_performance`, `revenue_brl` ≠ `revenue_usd × FX`: the BRL column includes freight, the USD column does not. If you need a freight-free BRL figure here, it is not currently exposed — derive it upstream from `item_price_brl`.

## Per-aggregate detail

### `mart_daily_revenue` — executive time series
Grain: one row per **active** calendar day (days with zero activity don't appear). Carries calendar attributes (`year`, `quarter`, `month`, `month_name`, `is_weekend`) so BI can slice by period and weekend without its own date logic.

| Column | KPI | Notes |
|---|---|---|
| `gmv_brl` | GMV | goods + freight; the headline revenue line |
| `items_brl` / `items_usd` / `items_eur` | Merchandise revenue | goods only; USD/EUR via daily FX |
| `freight_brl` | Freight | `gmv_brl − items_brl` |
| `n_orders` / `n_items` / `n_sellers` | Volume | distinct orders, lines, distinct sellers |

### `mart_category_revenue` — category mix
Grain: one row per **English category name**; products with no category map to `'unknown'` rather than being dropped. An order spanning two categories counts toward **both** — correct for category analysis, but means `n_orders` and `revenue_brl` are **not** summable to a company total across rows.

### `mart_state_performance` — regional map
Grain: one row per **customer state**. Uses the order-header fact, so revenue is counted once per order. Delivery KPIs are computed over **delivered orders only** — non-delivered orders have no delivery date to judge and are excluded from `on_time_pct`'s denominator. `n_delivered` and `n_on_time` are exposed so the ratio can be safely re-aggregated (sum the components, then divide — never average `on_time_pct`).

### `mart_seller_performance` — seller scorecard
Grain: one row per **seller**. Revenue/volume from line items; rating is the average review score across the seller's orders, mapped in through distinct `(seller, order)` pairs. An order with two sellers contributes its review to **both** sellers' averages — acceptable for a seller-level rating, but it means a global average review score is not the row-wise mean of this column. Sellers with no reviews show `avg_review_score = null` and `n_reviews = 0` (left join).

### `mart_customer_cohorts` — customer retention
Grain: one row per **acquisition month** (the month of a customer's first order). Customers are identified by `customer_unique_id`, so a shopper appears in exactly one cohort and `n_customers` sums to the true unique-customer total. `repeat_rate_pct`, `avg_orders_per_customer`, and `avg_clv_brl` are **per-customer ratios/averages — re-derive from components when rolling up across cohorts** (`Σ n_repeat_customers / Σ n_customers`, etc.), never average the percentage. `gmv_brl` here is lifetime cohort GMV (goods + freight, header fact), so it sums to the same grand total as the daily and state marts. All placed orders count — status is not filtered, so a cohort's `total_orders` reconciles to the full order count.

## Known reconciliation points

| Check | Expectation |
|---|---|
| Σ `mart_daily_revenue.gmv_brl` | = Σ `mart_category_revenue.revenue_brl` (both are line-item goods + freight over the same fact) |
| Σ `mart_state_performance.gmv_brl` | = above, *only* if every order resolves to a customer state and a line total — header vs. line-item grain can diverge on orders with no items |
| `revenue_brl` vs `revenue_usd` (category, seller) | will **not** reconcile at FX rate — BRL includes freight, USD does not (see ¹) |
| Σ `n_orders` across category or seller | **over-counts** — multi-category / multi-seller orders double-count by design |
| Σ `mart_customer_cohorts.n_customers` | = 96,096 (distinct `customer_unique_id`); Σ `total_orders` = 99,441; Σ `gmv_brl` = 15,843,553 BRL — all tie to the grand totals (verified dev + prod) |
