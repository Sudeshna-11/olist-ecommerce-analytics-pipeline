# Olist E-Commerce Analytics Pipeline

> Production-grade data pipeline for a real Brazilian e-commerce dataset.
> **Stack:** Python · Postgres → Snowflake · dbt · Airflow · Power BI · Docker · Terraform · GitHub Actions

**Status:** Week 2 of 8 — Snowflake migration in progress

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

# 2. Copy env template (edit credentials if you want)
Copy-Item .env.example .env

# 3. Set up Python virtual env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Spin up Postgres in Docker
docker compose up -d

# 5. Download Olist CSVs into data/raw/  (see data/README.md)

# 6. Load CSVs into Postgres
python -m src.ingest.load_olist

# 7. Verify row counts match expected
python -m src.ingest.verify_load
```

After step 6 you'll have 9 raw tables in the `raw` schema of the `olist` database. Step 7 fails loudly if anything is off.

## Switching to Snowflake (week 2)

The loader dispatches on the `TARGET` env var. To write to Snowflake instead of Postgres:

1. Fill in the `SNOWFLAKE_*` block in `.env` (see `.env.example` for the variable names; note `SNOWFLAKE_ACCOUNT` uses `orgname-accountname` with a **hyphen**).
2. Set `TARGET=snowflake` in `.env`.
3. Re-run the same commands:

```powershell
python -m src.ingest.load_olist     # writes to Snowflake OLIST.RAW
python -m src.ingest.verify_load    # verifies against Snowflake
```

The underlying bulk-load path is target-specific: Postgres uses `COPY FROM STDIN`, Snowflake uses `write_pandas` (internal stage + `COPY INTO`). The orchestrator and the row-count manifest are shared.

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
| 2 | Snowflake + Python | Migrate ingestion to Snowflake; add live FX rates API | Snowflake done, FX rates pending |
| 3 | dbt | Staging + marts layers with tests and dbt docs | |
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
│   └── targets/          # Per-backend modules (postgres.py, snowflake.py)
├── tests/                # pytest unit + integration tests
├── docker-compose.yml    # Local Postgres
├── pyproject.toml        # pytest config
├── requirements.txt      # Python deps (runtime)
├── requirements-dev.txt  # Python deps (+ pytest)
├── .env.example          # Env var template
└── README.md
```

Folders for `dbt/`, `airflow/`, `dashboards/`, `terraform/`, and `.github/workflows/` are added in their respective weeks — kept out for now to keep the repo focused.

## License

MIT
