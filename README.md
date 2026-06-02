# Olist E-Commerce Analytics Pipeline

> Production-grade data pipeline for a real Brazilian e-commerce dataset.
> **Stack:** Python · Postgres → Snowflake · dbt · Airflow · Power BI · Docker · Terraform · GitHub Actions

**Status:** Week 3 of 8 — full dbt staging layer (10 models, 48 tests) green against Postgres

---

## What this project does

This is a real, working data pipeline that:

1. **Ingests** raw e-commerce orders from the public [Brazilian Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (~100K orders, 9 source tables).
2. **Lands** them in a cloud data warehouse (Snowflake).
3. **Transforms** them into analytics-ready tables using dbt (staging → marts).
4. **Schedules** daily refreshes via Airflow.
5. **Visualizes** business KPIs in a Power BI dashboard.

The whole thing runs in Docker locally and on AWS in production.

## Why this matters

For an e-commerce business, the marts layer answers questions like:

- Which product categories drive the most revenue?
- Where are our customers concentrated geographically?
- What's our average delivery time vs. estimated, by region?
- Which sellers are top-rated vs. lowest-rated?

## Data modeling

This project uses **medallion layering (bronze/silver/gold) with a Kimball star schema at the gold layer** — the modern dbt-standard architecture. Full design in [docs/data-modeling.md](docs/data-modeling.md).

- **Bronze** (raw schema) — 9 source tables, 1:1 with CSVs
- **Silver** — staging (clean/rename) → intermediate (reusable business logic)
- **Gold** — Kimball facts (`fct_orders`, `fct_order_items`, `fct_order_reviews`) and dimensions (`dim_customers`, `dim_products`, `dim_sellers`, `dim_dates`) + dashboard aggregates

Demonstrated concepts: layered architecture, surrogate keys, conformed dimensions, two facts at different grains, SCD Type 2 (via dbt snapshots), generated date dimension, dbt source freshness, incremental models, data quality tests, dbt docs lineage graph.

## Architecture (target state, end of week 8)

```
   [Olist CSVs]          [FX rates API]
        │                      │
        └──────────┬───────────┘
                   ▼
            Python ingest
          (Docker container)
                   │
                   ▼
            Snowflake (raw schema)
                   │
                   ▼  dbt: staging → intermediate → marts
            Snowflake (analytics schema)
                   │
                   ▼
            Power BI dashboard

   Orchestration: Airflow DAG (daily)
   Infra:         Terraform on AWS (ECS Fargate)
   CI/CD:         GitHub Actions (lint, dbt test, deploy)
   Quality:       dbt tests + Great Expectations
```

## Quick start (week 1 — local)

Prereqs: Docker Desktop, Python 3.10+, Git.

```powershell
# 1. Clone
git clone <this-repo>
cd data_engineer_project

# 2. Copy env templates (secrets live in .secrets.env, everything else in .env)
Copy-Item .env.example .env
Copy-Item .secrets.env.example .secrets.env
# then edit .secrets.env to put real passwords/API keys in it

# 3. Set up Python virtual env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Spin up Postgres in Docker
docker compose up -d

# 5. Download Olist CSVs into data/raw/  (see data/README.md)

# 6. Load CSVs into Postgres (or Snowflake if TARGET=snowflake)
python -m src.ingest.load_olist

# 7. Fetch FX rates from Frankfurter (BRL -> USD, EUR; 2016-09..2018-12)
python -m src.ingest.fx_rates

# 8. Verify row counts match expected
python -m src.ingest.verify_load
```

After steps 6-7 you'll have 10 raw tables in the `raw` schema. Step 8 fails loudly if anything is off.

## Configuration split: `.env` vs `.secrets.env`

The loader merges two dotenv files at runtime:

- **`.env`** — non-sensitive config (TARGET, hostnames, ports, usernames, warehouse/database names). Safe to share, paste into bug reports, etc.
- **`.secrets.env`** — passwords, API keys, tokens. Gitignored. Loaded with `override=True` so it always wins.

Both files have a `.example` template committed for reference. The split exists so you can share or screenshot `.env` without leaking credentials, and so a stale password in `.env` can't silently override the real one in `.secrets.env`.

## Switching to Snowflake (week 2)

The loader dispatches on the `TARGET` env var. To write to Snowflake instead of Postgres:

1. Fill the non-secret `SNOWFLAKE_*` vars (account, user, warehouse, etc.) in `.env`; put `SNOWFLAKE_PASSWORD` in `.secrets.env`. Note `SNOWFLAKE_ACCOUNT` uses `orgname-accountname` with a **hyphen**, not the slash from the Snowsight URL.
2. Set `TARGET=snowflake` in `.env`.
3. Re-run the same commands:

```powershell
python -m src.ingest.load_olist     # writes to Snowflake OLIST.RAW
python -m src.ingest.verify_load    # verifies against Snowflake
```

The underlying bulk-load path is target-specific: Postgres uses `COPY FROM STDIN`, Snowflake uses `write_pandas` (internal stage + `COPY INTO`). The orchestrator and the row-count manifest are shared.

## dbt (week 3)

The dbt project lives in [`olist_dbt/`](olist_dbt/) and uses the same `.env`/`.secrets.env` split via a thin wrapper:

```powershell
pip install -r requirements-dev.txt        # installs dbt-core, dbt-postgres, dbt-snowflake

python scripts/dbt.py debug                 # verify connection
python scripts/dbt.py deps                  # install dbt_utils
python scripts/dbt.py run --select staging  # build the staging layer
python scripts/dbt.py test                  # run not_null / unique / accepted_values / relationships
```

The wrapper calls `src.ingest.config.load_env()` then dispatches to `dbt` with `--project-dir olist_dbt --profiles-dir olist_dbt` baked in. Equivalent raw command (if your shell already has the env vars set):

```powershell
dbt run --project-dir olist_dbt --profiles-dir olist_dbt --select staging
```

Two profile targets are defined in `olist_dbt/profiles.yml`:

- **`dev` (default)** → local Postgres. Free, fast iteration. All weeks-3 development happens here.
- **`prod`** → Snowflake. `python scripts/dbt.py run --target prod` to deploy.

The same SQL runs against both backends. Materialization defaults: `staging` = view, `intermediate` = ephemeral, `marts` = table. Naming convention `stg_<source>__<entity>` per the dbt style guide.

## Tests

```powershell
pip install -r requirements-dev.txt

# Unit tests only (no DB needed)
pytest -m "not integration"

# Full suite (requires Postgres running with the load complete)
pytest
```

## Roadmap

| Week | Theme | Deliverable | Status |
|---|---|---|---|
| 1 | Foundations | Project skeleton + Docker Postgres + Olist ingestion script | Done |
| 2 | Snowflake + Python | Migrate ingestion to Snowflake; add live FX rates API | Done |
| 3 | dbt | Staging + marts layers with tests and dbt docs | In progress |
| 4 | Power BI | Executive / Regional / Customer dashboards | |
| 5 | Airflow | Daily orchestration DAG, failure alerts | |
| 6 | Terraform + AWS | Deploy Airflow to ECS Fargate | |
| 7 | CI/CD + Quality | GitHub Actions; Great Expectations | |
| 8 | Polish | Architecture diagram, Loom walkthrough, business outcome write-up | |

## Tech choices and why

| Layer | Tool | Why |
|---|---|---|
| Local storage | Postgres (Docker) | Free, ubiquitous, identical SQL to most warehouses |
| Cloud warehouse | Snowflake | #1 most-requested warehouse on Upwork data gigs |
| Transformation | dbt-core | Industry standard; recruiters search for it by name |
| Orchestration | Airflow | Most-listed orchestrator in current job postings |
| Dashboard | Power BI | #1 BI tool on Upwork |
| Containers | Docker + docker-compose | Reproducibility = trust |
| Infra-as-code | Terraform on AWS | Signals "real engineer" |
| Quality | dbt tests + Great Expectations | Data quality is the #1 client ask |
| CI/CD | GitHub Actions | Free, ubiquitous, recruiters look for green badges |

## Project layout

```
data_engineer_project/
├── data/raw/             # Olist CSVs (gitignored — see data/README.md)
├── docs/                 # Architecture diagrams, decisions
├── src/ingest/           # Python ingestion + verification
│   ├── config.py         # Dual-file env loader (.env + .secrets.env)
│   ├── expected.py       # Canonical row-count manifest
│   ├── load_olist.py     # CSV -> warehouse orchestrator (TARGET-dispatched)
│   ├── fx_rates.py       # Frankfurter API -> raw_fx_rates
│   ├── verify_load.py    # Post-load row-count check
│   └── targets/          # Per-backend modules (postgres.py, snowflake.py)
├── olist_dbt/            # dbt project (week 3) — staging/intermediate/marts
│   ├── dbt_project.yml
│   ├── profiles.yml      # dev=Postgres, prod=Snowflake; reads env_var()
│   ├── packages.yml      # dbt_utils
│   └── models/staging/   # stg_olist__* + _sources.yml + _schema.yml
├── scripts/dbt.py        # Wrapper: load_env() then dispatch to dbt
├── tests/                # pytest unit + integration tests
├── docker-compose.yml    # Local Postgres
├── pyproject.toml        # pytest config
├── requirements.txt      # Python deps (runtime)
├── requirements-dev.txt  # Python deps (+ pytest, dbt)
├── .env.example          # Non-secret env var template
├── .secrets.env.example  # Secret env var template (passwords, API keys)
└── README.md
```

Folders for `airflow/`, `dashboards/`, `terraform/`, and `.github/workflows/` are added in their respective weeks — kept out for now to keep the repo focused.

## License

MIT
