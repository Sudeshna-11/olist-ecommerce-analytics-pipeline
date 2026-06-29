#!/usr/bin/env bash
# One-shot pipeline run for the Fargate task: ingest -> verify -> dbt build.
# Mirrors the week-5 Airflow DAG's task order, collapsed into a single container.
#
# Env:
#   TARGET             backend selector (default snowflake)
#   RAW_DATA_S3_URI    if set, sync raw CSVs from here at startup (cloud path).
#                      If unset, data/raw is expected to already be present
#                      (e.g. bind-mounted) — the local test path.
#   SNOWFLAKE_*        injected from Secrets Manager by the ECS task definition.
set -euo pipefail

cd /opt/project
export TARGET="${TARGET:-snowflake}"
mkdir -p data/raw

if [ -n "${RAW_DATA_S3_URI:-}" ]; then
  echo ">> Syncing raw data from ${RAW_DATA_S3_URI}"
  aws s3 sync "${RAW_DATA_S3_URI}" data/raw
else
  echo ">> RAW_DATA_S3_URI unset; using existing data/raw (local mode)"
fi

echo ">> [1/8] load_olist"
python -m src.ingest.load_olist
echo ">> [2/8] fx_rates"
python -m src.ingest.fx_rates
echo ">> [3/8] verify_load"
python -m src.ingest.verify_load

echo ">> [4/8] dbt deps"
python scripts/dbt.py deps
echo ">> [5/8] dbt run (staging)"
python scripts/dbt.py run --target prod --select staging
echo ">> [6/8] dbt snapshot"
python scripts/dbt.py snapshot --target prod
echo ">> [7/8] dbt run (marts)"
python scripts/dbt.py run --target prod --exclude staging
echo ">> [8/8] dbt test"
python scripts/dbt.py test --target prod

echo ">> Pipeline complete."
