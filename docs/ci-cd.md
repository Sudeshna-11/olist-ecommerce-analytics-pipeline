# CI/CD & Data Quality

Continuous integration for the Olist pipeline. Every push to `main` and every
pull request runs [`.github/workflows/ci.yml`](../.github/workflows/ci.yml),
which exercises the **entire pipeline** — not just unit tests — using an
ephemeral Postgres and a committed data sample, with **no credentials**.

## The three jobs

```
┌──────────────────────┐   ┌─────────────────────────────────────────────┐   ┌────────────────────┐
│ unit                 │   │ integration  (Postgres service container)   │   │ docker-build       │
│ ruff + pytest        │   │ ingest → fx → verify → GE gate → dbt → test  │   │ build deploy image │
│ (-m "not integration")│  │ on tests/fixtures/sample_raw/               │   │ (Fargate Dockerfile)│
└──────────────────────┘   └─────────────────────────────────────────────┘   └────────────────────┘
```

| Job | Steps | Why |
|-----|-------|-----|
| **`unit`** | `ruff check` then `pytest -m "not integration"` | Fast feedback; pure-Python, no services or secrets. |
| **`integration`** | Ingest sample → load FX (offline) → row-count verify → **Great Expectations source gate** → `dbt deps / run staging / snapshot / run marts / test` → `pytest -m integration` | Proves the real pipeline runs end-to-end and the gold star schema still passes all 127 dbt tests. |
| **`docker-build`** | `docker build -f deploy/Dockerfile` | Catches breakage in the cloud image before a deploy would. |

## Why a committed sample

The integration job needs data, but the 9 Olist CSVs are gitignored
(`data/raw/*`) and require a Kaggle account to download — so CI can't load the
real thing. The options were:

1. **Unit tests only in CI** — leaves dbt, the star schema, and data quality
   completely untested in CI. Weak.
2. **Download the CSVs in CI** — needs Kaggle credentials as repo secrets and
   couples every CI run to an external download. Fragile.
3. **Commit a small, referentially-consistent sample** ✅ — self-contained,
   credential-free, deterministic, and exercises the full pipeline.

We chose option 3 (see [ADR-011](architecture.md#decisions-log-adrs)).

### How the sample stays valid

dbt enforces `relationships` and `unique` tests across the star schema, so a
naive `head -n 500` of each CSV would fail instantly (an order item pointing at
a product that wasn't sampled). [`scripts/make_sample.py`](../scripts/make_sample.py)
instead carves a **closed slice of the foreign-key graph**:

```
orders            ← random sample of N order_ids (the seed set)
  customers       ← the customer behind each sampled order
  order_items     ← items for those orders → product_ids, seller_ids
    products      ← products referenced by those items
    sellers       ← sellers referenced by those items
  order_payments  ← payments for those orders
  order_reviews   ← reviews for those orders
  geolocation     ← rows for every zip prefix a kept customer/seller uses
category_translation ← kept whole (71 rows)
```

Because every child's parents are pulled in, the sample passes **all 127 dbt
tests** exactly as the full dataset does. Geolocation is capped to a few rows
per zip prefix (`--geo-per-zip`, default 3) — the centroid model averages them,
so a handful per prefix reproduces the join while keeping the fixture small
(~550 KB total). FX rates are fetched once for the full production date range and
written to `olist_fx_rates_sample.csv`, so the forward-fill always covers the
sampled order dates.

The generator also writes `_manifest.json` (table → row count), which the
row-count check validates against.

Regenerate after changing the carving logic:

```bash
python scripts/make_sample.py --orders 500
```

## Two layers of data tests

Great Expectations and dbt are split **by layer**, not overlapped
(see [ADR-012](architecture.md#decisions-log-adrs)):

| Framework | Layer | Role | Example expectations |
|-----------|-------|------|----------------------|
| **Great Expectations** | raw (bronze), post-ingest | Independent **source contract** — catch bad source data at the door | `order_id` not null & unique · `review_score ∈ [1,5]` · `payment_type ∈ {credit_card, boleto, …}` · `price ≥ 0` · valid lat/lng · table not empty |
| **dbt tests** | staging + gold | **Modelled correctness** — grain, conformance, referential integrity | not-null, unique, accepted-values, relationships, surrogate-key uniqueness (127 tests) |

The source gate lives in [`scripts/ge_validate.py`](../scripts/ge_validate.py):
one in-code expectation suite per raw table, run with an ephemeral GX context
against the same Postgres the loader writes to. It prints a per-table summary
and exits non-zero on any violation:

```
Great Expectations source gate - schema 'raw'

  [OK  ] raw_orders                 6/6 expectations (500 rows)
  [OK  ] raw_order_items            5/5 expectations (568 rows)
  ...
  Source gate PASSED: all 10 raw tables meet their contract.
```

Run it locally against the full warehouse any time:

```bash
TARGET=postgres python scripts/ge_validate.py
```

## Running the integration sequence locally

The CI integration job is reproducible on any machine with the local Postgres up
(`docker compose up -d`). Point the pipeline at the sample and an isolated
database so it doesn't touch your dev data:

```bash
docker exec olist_postgres psql -U olist_user -d olist -c "CREATE DATABASE olist_citest;"

export TARGET=postgres POSTGRES_DB=olist_citest \
       POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
       POSTGRES_USER=olist_user POSTGRES_PASSWORD=olist_pass \
       OLIST_RAW_DIR=tests/fixtures/sample_raw \
       OLIST_EXPECTED_COUNTS=tests/fixtures/sample_raw/_manifest.json \
       FX_RATES_CSV=tests/fixtures/sample_raw/olist_fx_rates_sample.csv

python -m src.ingest.load_olist
python -m src.ingest.fx_rates
python -m src.ingest.verify_load
python scripts/ge_validate.py
python scripts/dbt.py deps
python scripts/dbt.py run --select staging
python scripts/dbt.py snapshot
python scripts/dbt.py run --exclude staging
python scripts/dbt.py test
pytest -m integration
```

## Env hooks added for CI

To run the production code against a sample without forking it, three optional
env vars were added — all default to the normal full-dataset behaviour when unset:

| Env var | Read by | Effect |
|---------|---------|--------|
| `OLIST_RAW_DIR` | `src/ingest/load_olist.py` | Directory the loader reads CSVs from (default `data/raw`). |
| `OLIST_EXPECTED_COUNTS` | `src/ingest/expected.py` | Path to a JSON row-count manifest; overrides the hard-coded full-dataset counts used by `verify_load` and the integration test. |
| `FX_RATES_CSV` | `src/ingest/fx_rates.py` | Load FX from a local CSV instead of calling Frankfurter — keeps CI hermetic. |

## Notes & possible extensions

- **No secrets in CI.** The integration job uses a throwaway Postgres service;
  Snowflake is never contacted. Production correctness on Snowflake is proven
  separately by the week-5/6 runs.
- The deploy image installs `requirements-dev.txt`, so Great Expectations and
  ruff currently ride along into it. If image size becomes a concern, split
  CI-only tooling into a separate requirements file.
- Natural next steps: SQL linting of dbt models (`sqlfluff`), a scheduled
  nightly run against Snowflake, and publishing the dbt docs site as a CI
  artifact.
