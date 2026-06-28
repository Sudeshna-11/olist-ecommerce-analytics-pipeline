# Airflow orchestration

Daily orchestration of the Olist pipeline — ingest the raw CSVs and FX rates,
verify the load, then run and test every dbt model against **Snowflake prod**,
so the published Power BI report refreshes nightly.

## The DAG — `olist_daily_pipeline`

```
load_olist ─┐
            ├─> verify_load ─> dbt deps ─> dbt run (staging)
fx_rates  ──┘                          ─> dbt snapshot
                                       ─> dbt run (marts) ─> dbt test
```

| Task | Command (in the project venv) | Purpose |
|------|-------------------------------|---------|
| `load_olist` | `python -m src.ingest.load_olist` | 9 Olist CSVs → `raw` schema |
| `fx_rates` | `python -m src.ingest.fx_rates` | Frankfurter BRL→USD/EUR → `raw_fx_rates` |
| `verify_load` | `python -m src.ingest.verify_load` | Row-count gate; fails the run on any mismatch |
| `dbt_deps` | `python scripts/dbt.py deps` | Install `dbt_utils` |
| `dbt_run_staging` | `python scripts/dbt.py run --target prod --select staging` | Build the staging views (the snapshot's source) |
| `dbt_snapshot` | `python scripts/dbt.py snapshot --target prod` | SCD2 snapshot of the product catalogue (source of `dim_products`) |
| `dbt_run_marts` | `python scripts/dbt.py run --target prod --exclude staging` | Build the intermediate + mart tables |
| `dbt_test` | `python scripts/dbt.py test --target prod` | 126 data-quality tests |

The dbt stage is split because the SCD2 snapshot sits mid-graph: it reads the
staging views and feeds `dim_products`, so staging must be built first, then
the snapshot taken, then the marts built and tested.

- **Schedule:** `0 7 * * *` (daily 07:00), `catchup=False`, `max_active_runs=1`.
- **Retries:** 2 per task, 5-minute backoff.
- **On failure:** posts a summary to the Slack webhook in `SLACK_WEBHOOK_URL`
  (degrades to a logged warning if unset — alerting never fails the run).

## How it's wired

- **LocalExecutor** — three containers: a metadata Postgres, the webserver, and
  the scheduler. No Celery / redis / worker.
- **Isolated dependency trees.** Airflow needs SQLAlchemy 1.4; the project pins
  SQLAlchemy 2.0 and brings dbt + the Snowflake connector. So the image builds a
  separate venv at `/opt/project-venv` for the pipeline, and the DAG calls that
  interpreter directly (`BashOperator`). Airflow never imports the project.
- **No copied code.** The repo root is mounted at `/opt/project`, so tasks run
  the real `src/`, `scripts/dbt.py`, `olist_dbt/` and `data/raw/`.
- **Credentials** are read from the project's `../.env` + `../.secrets.env` — the
  same files the CLI uses. Nothing secret lives in this folder.

## Run it

Prereqs: Docker Desktop running; `.env` and `.secrets.env` present at the repo
root with valid `SNOWFLAKE_*` values; the Olist CSVs in `data/raw/`.

```powershell
# 1. (optional) enable Slack alerts — add to .secrets.env at the repo root:
#    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ

# 2. from this airflow/ folder — build the image and start the stack
docker compose up -d --build

# 3. open the UI, log in admin / admin
start http://localhost:8080

# 4. un-pause and trigger the DAG (or wait for 07:00)
#    UI: toggle "olist_daily_pipeline" on, then ▶ Trigger
#    or CLI:
docker compose exec airflow-scheduler airflow dags trigger olist_daily_pipeline

# tear down (keep the metadata volume)
docker compose down
# tear down and wipe metadata
docker compose down -v
```

First `up --build` takes a few minutes (it installs the project venv into the
image). The DAG ships paused (`DAGS_ARE_PAUSED_AT_CREATION=true`); toggle it on
in the UI to schedule it.

## Notes

- This runs against **Snowflake**, so each full run burns a small amount of
  credits. To smoke-test cheaply, point the dbt tasks at `--target dev` (local
  Postgres) — but note the local Postgres host isn't reachable from the
  container as `localhost`, so the ingest steps would need the Postgres service
  on the same Docker network first.
- The Olist source CSVs are a fixed historical dataset, so a daily *ingest* is
  demonstrative; the FX feed and the dbt build are the parts that genuinely
  benefit from a daily cadence.
