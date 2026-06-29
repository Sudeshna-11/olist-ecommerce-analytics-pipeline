# Pipeline container (week 6)

A single image that runs the whole Olist pipeline end-to-end in one shot:

```
ingest (CSV + FX) -> verify -> dbt deps/run/snapshot/run/test  (--target prod)
```

It's the production runtime for week 6: **EventBridge Scheduler** launches it as
an **ECS Fargate** task daily. The week-5 Airflow stack is unchanged and stays
the local/dev orchestrator — this is the cloud trigger.

| File | Purpose |
|---|---|
| `Dockerfile` | `python:3.11-slim` + project deps (incl. dbt + Snowflake connector) + AWS CLI v2. Build context is the repo root. |
| `entrypoint.sh` | Runs the 8 pipeline steps in DAG order. Pulls raw CSVs from S3 if `RAW_DATA_S3_URI` is set, else uses a mounted `data/raw`. |

## Configuration (env)

| Var | In cloud | Locally |
|---|---|---|
| `TARGET` | `snowflake` (ECS task def) | from `.env` (default `snowflake` in entrypoint) |
| `SNOWFLAKE_*` | injected from Secrets Manager | from `.secrets.env` via `--env-file` |
| `RAW_DATA_S3_URI` | `s3://<raw-bucket>/raw` (ECS task def) | unset → uses mounted `data/raw` |

No code change versus the CLI/Airflow paths: `config.load_env()` treats the env
files as optional and `profiles.yml` reads everything via `env_var()`, so
environment variables alone are enough.

## Build

```bash
# from the repo root (the build context)
docker build -f deploy/Dockerfile -t olist-pipeline:local .
```

## Run locally against Snowflake

```bash
# read-only connectivity check (no writes, no credits)
docker run --rm --env-file .env --env-file .secrets.env \
  --entrypoint python olist-pipeline:local scripts/dbt.py debug --target prod

# full pipeline (mutates Snowflake prod — same as a normal run)
docker run --rm --env-file .env --env-file .secrets.env \
  -v "$(pwd)/data/raw:/opt/project/data/raw" \
  olist-pipeline:local
```

In the cloud the CSVs come from S3 instead of the bind mount, and the secrets
come from Secrets Manager instead of `--env-file`.
