# Architecture

Detailed architecture, decisions, and diagrams will land here over the next 8 weeks. For now, see the high-level diagram in the [project README](../README.md).

## Decisions log (ADRs)

| # | Date | Decision | Status |
|---|---|---|---|
| 001 | 2026-05-17 | Use Postgres locally (week 1) before moving to Snowflake (week 2) | Accepted |
| 002 | 2026-05-17 | Use dbt-core (not dbt Cloud) for transformations | Accepted |
| 003 | 2026-05-17 | Airflow for orchestration; alternatives considered: Prefect, Dagster | Accepted |
| 004 | 2026-05-17 | **Medallion layering (bronze/silver/gold) with Kimball star schema at the gold layer.** See [data-modeling.md](data-modeling.md) for the full design. | Accepted |
| 005 | 2026-05-18 | Loader uses a per-backend module under `src/ingest/targets/` (`postgres.py`, `snowflake.py`) selected via the `TARGET` env var. Postgres bulk-loads via `COPY FROM STDIN`; Snowflake via `write_pandas` (internal stage + `COPY INTO`). | Accepted |
| 006 | 2026-05-18 | Configuration split into `.env` (non-secrets) and `.secrets.env` (passwords/API keys, gitignored). `src/ingest/config.py:load_env()` loads both with `override=True` on the secrets pass. Motivation: keep credentials out of any context where `.env` is read or shared (issue reports, chat transcripts). | Accepted |
| 007 | 2026-05-18 | FX rates sourced from api.frankfurter.app (free, no API key, ECB-backed). Fetched for the date range bracketing Olist orders and landed as long-format `raw_fx_rates` (date, base, quote, rate) via the same target-dispatch as Olist CSVs. | Accepted |
| 008 | 2026-06-01 | **dbt project layout for week 3.** Single project at `olist_dbt/` (sibling to `src/`), with `profiles.yml` checked into the repo (not `~/.dbt/`). Two targets: `dev` → Postgres (default, used for iteration), `prod` → Snowflake (deploy + `dbt docs`). Same SQL runs against both; macros via `dbt_utils` only. Credentials sourced from the existing `.env`/`.secrets.env` via a thin `scripts/dbt.py` wrapper that calls `load_env()` before dispatching to `dbt`, so no creds live in `profiles.yml` and no shell sourcing is needed on Windows. Materialization defaults: staging=view, intermediate=ephemeral, marts=table. Naming convention `<layer>_<source>__<entity>` per the official dbt style guide. | Accepted |
