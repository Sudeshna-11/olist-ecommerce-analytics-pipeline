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
