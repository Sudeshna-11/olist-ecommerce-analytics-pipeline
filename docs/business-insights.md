# Olist E-Commerce: Build & Insights

A case study of this project from both sides: the **engineering** that turns nine
raw CSVs into a tested, query-ready warehouse, and the **business findings** that
warehouse produces. Every figure below is queried live from the gold marts
(`analytics_marts`) on the full dataset — not hand-copied — so each number is
traceable to a model. See [architecture.md](architecture.md) for the full system
design and [data-modeling.md](data-modeling.md) for the star schema.

---

## 1. The business and the questions

[Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) is a
Brazilian marketplace that connects small sellers to customers across the major
e-commerce sites. The public dataset covers **99,441 orders** placed between
**September 2016 and October 2018** (~25 months), worth **R$15.84M** in
merchandise. The questions a marketplace operator would ask of it:

1. How big is the business, and how is it growing?
2. Are we delivering on time — and does delivery actually matter to customers?
3. Do customers come back?
4. Where is revenue concentrated — geography, category, sellers — and what's the risk?
5. How do Brazilians pay, and why does it matter?

## 2. How it's built (the short version)

Raw CSVs are ingested with Python into a warehouse, then transformed with **dbt**
into a **Kimball star schema** following **medallion (bronze → silver → gold)**
layering. The same dbt code runs on **Postgres** (local dev) and **Snowflake**
(prod), passing **127 tests** identically on both. The daily pipeline is
orchestrated by **Airflow** in dev and a scheduled **ECS Fargate** task in the
cloud, all provisioned with **Terraform** and gated by **GitHub Actions CI** +
**Great Expectations**. Five pre-aggregated marts feed a 5-page **Power BI**
report. Full detail in [architecture.md](architecture.md).

The findings below come from that gold layer — specifically the fact tables
(`fct_orders`, `fct_order_reviews`) and the five aggregate marts.

## 3. Key findings

### Scale & growth

| Metric | Value |
|--------|------:|
| Orders | 99,441 (96,478 delivered, 97%) |
| Merchandise value (GMV) | R$15.84M |
| Total paid (incl. freight, fees) | R$16.01M |
| Average order value | R$159.33 |
| Items per order | 1.13 |
| Freight as % of GMV | 14.2% |

The marketplace grew from a near-zero launch (Sept 2016) to a **Black Friday 2017
peak of 7,544 orders / R$1.18M in a single month**. Two patterns stand out
immediately: orders are **small and single-item** (1.13 items, R$159 average), so
this is a high-frequency, low-basket business; and **freight is a material 14%**
of merchandise value, making logistics both a cost centre and — as the next
finding shows — the key to satisfaction.

### Delivery is the single biggest driver of customer satisfaction

This is the headline insight. Average delivery is **12.5 days** (median 10), and
**91.9%** of orders arrive on or before the estimated date. But the impact of the
**8.1% that arrive late** is severe:

| Delivery outcome | Avg review score | % 1-star reviews |
|------------------|-----------------:|-----------------:|
| **On-time** | 4.29 ★ | 6.6% |
| **Late** | 2.57 ★ | 46.2% |

A late delivery costs **1.7 stars** on average, and nearly **half** of late
orders get a 1-star review. Overall satisfaction is decent (4.09 average, 57.8%
five-star), but it is almost entirely gated by hitting the delivery date.

One nuance: delivery **estimates are conservative** — the average promised window
is 24.4 days but parcels arrive ~12 days early. The estimate is effectively a
safety buffer, which protects the on-time rate. The lever isn't tighter promises;
it's faster actual delivery where it lags (see geography).

### Customers don't come back — this is an acquisition business

| Metric | Value |
|--------|------:|
| Unique customers | 96,096 |
| Customers with a repeat purchase | 2,997 |
| **Overall repeat rate** | **3.12%** |

Only **~3 in 100 customers ever order again**. (Measured on `customer_unique_id`,
the true person key — Olist issues a fresh `customer_id` per order, a quirk that
would show a near-0% repeat rate if measured naively.) The marketplace runs almost
entirely on new-customer acquisition. That's the largest single opportunity in the
dataset: because acquisition cost is paid once, even a few points of repeat-rate
lift compounds directly into margin.

### Revenue is highly concentrated — strength and risk

- **Geography:** São Paulo state alone is **R$5.92M (37% of GMV)**; the **top 3
  states are 62.5%** of all revenue. SP is also the *fastest and most reliable*:
  **8.7-day** delivery and **94.1%** on-time, versus **15.5 days / 90.3%** for the
  rest of the country. The logistics network is effectively SP-centric.
- **Category:** 72 categories, but the **top 10 are 62%** of revenue, led by
  *health & beauty* (R$1.44M), *watches & gifts* (R$1.31M) and *bed/bath/table*
  (R$1.24M).
- **Sellers:** of **3,095 sellers**, the **top 10% earn 66.8%** of revenue — a
  classic marketplace power-law.

Concentration cuts both ways: it's operational focus today, and single-point risk
(one region, a handful of sellers) tomorrow.

### Payment behaviour: instalments are core to conversion

**51.5%** of orders are paid in instalments (averaging ~3 instalments where used).
Brazilian *parcelamento* isn't a fringe option — it's how the majority buy, even at
a R$159 average ticket. Anything that degrades the instalment experience (declines,
fewer instalment options) would directly suppress conversion.

## 4. Recommendations

1. **Treat delivery speed as the primary CX investment**, focused outside SP.
   Late delivery is the dominant cause of 1-star reviews, and the non-SP regions
   are both slower (15.5 vs 8.7 days) and less reliable. Regional fulfilment
   capacity is the highest-leverage fix.
2. **Stand up a retention motion.** At 3% repeat, there is effectively no
   lifecycle marketing. Post-delivery follow-up, category cross-sell (the
   single-item basket is an obvious expansion target), and a light loyalty
   mechanic would each move a metric that is currently near zero.
3. **De-risk concentration deliberately.** Grow seller supply and category breadth
   outside the top-10, and use the SP logistics playbook as the template for
   expanding reliable delivery into RJ and the south.
4. **Protect the instalment rail.** With half of orders financed, payment
   acceptance and instalment availability are conversion-critical, not back-office.

## 5. Caveats & data-quality notes

Intellectual honesty matters as much as the headline numbers:

- **Static snapshot.** The data is a fixed 2016–2018 export with no PII; figures
  describe a historical period, not a live business.
- **Documented duplicate reviews.** 0.8% of `review_id`s span multiple orders. This
  is surfaced (not silently fixed) via a `warn`-severity dbt test — a real data
  quality finding kept visible. The review fact is grained on `(review_id,
  order_id)` so it's correct regardless.
- **Customer key.** Retention is computed on `customer_unique_id`; using the
  per-order `customer_id` would be wrong (and is a common Olist analysis mistake).
- **Small early cohorts.** The first months have only a handful of customers, so
  early-cohort repeat rates are statistically noisy — the **3.12% overall** figure
  is the reliable one.

## 6. Reproducing the numbers

Every figure here comes from the gold marts. With the warehouse built
(`python scripts/dbt.py build`), they're one query away — e.g. the delivery →
review insight:

```sql
SELECT CASE WHEN o.is_late THEN 'late' ELSE 'on-time' END AS outcome,
       round(avg(r.review_score), 2)                       AS avg_score,
       round(100.0 * sum((r.review_score = 1)::int) / count(*), 1) AS pct_1star
FROM   analytics_marts.fct_order_reviews r
JOIN   analytics_marts.fct_orders o USING (order_id)
WHERE  o.is_delivered
GROUP  BY o.is_late;
```

See [metrics.md](metrics.md) for the full measure catalogue and how each maps to
its aggregate, currency, and additivity rules.
