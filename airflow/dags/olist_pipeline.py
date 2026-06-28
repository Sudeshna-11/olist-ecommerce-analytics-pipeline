"""Daily Olist pipeline: ingest (CSV + FX) -> verify -> dbt build on Snowflake.

Orchestrates the same entry points used from the CLI, run against the prod
(Snowflake) warehouse so the published Power BI report refreshes nightly:

    load_olist ─┐
                ├─> verify_load -> dbt deps -> dbt run (staging)
    fx_rates  ──┘                              -> dbt snapshot
                                               -> dbt run (marts) -> dbt test

dbt's SCD2 snapshot (dim_products' source) sits mid-graph: it reads the
staging views and feeds the marts. So staging is built first, the snapshot
is taken, then the marts are built and tested.

Pipeline code and dbt live in an isolated venv (/opt/project-venv) baked into
the Airflow image; the repo is mounted at /opt/project. Airflow only
orchestrates — it never imports the project, so their dependency trees stay
separate (Airflow needs SQLAlchemy 1.4, the project pins 2.0).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/project"
VENV_PY = "/opt/project-venv/bin/python"

# Force the prod (Snowflake) backend for the ingest steps regardless of the
# .env default. load_env() uses override=False, so this wins.
PIPELINE_ENV = {"TARGET": "snowflake"}


def notify_slack_on_failure(context) -> None:
    """Post a failure summary to the Slack webhook in SLACK_WEBHOOK_URL.

    Degrades to a logged warning if the webhook is unset, and swallows any
    posting error — alerting must never be the reason a run is marked failed.
    """
    import requests

    ti = context["task_instance"]
    text = (
        ":red_circle: *Olist pipeline failed*\n"
        f"*DAG*: {ti.dag_id}\n"
        f"*Task*: {ti.task_id}\n"
        f"*Run*: {context['run_id']}\n"
        f"*Log*: {ti.log_url}"
    )

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        logging.warning("SLACK_WEBHOOK_URL not set; skipping Slack alert.\n%s", text)
        return
    try:
        requests.post(webhook, json={"text": text}, timeout=10)
    except Exception as exc:  # noqa: BLE001 - never break the run on alert failure
        logging.error("Slack alert failed: %s", exc)


default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_slack_on_failure,
}


def ingest_cmd(module: str) -> str:
    return f"cd {PROJECT_DIR} && {VENV_PY} -m {module}"


def dbt_cmd(args: str) -> str:
    return f"cd {PROJECT_DIR} && {VENV_PY} scripts/dbt.py {args}"


with DAG(
    dag_id="olist_daily_pipeline",
    description="Daily ingest + dbt build of the Olist warehouse on Snowflake",
    schedule="0 7 * * *",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["olist", "week5", "snowflake"],
) as dag:

    load_olist = BashOperator(
        task_id="load_olist",
        bash_command=ingest_cmd("src.ingest.load_olist"),
        env=PIPELINE_ENV,
        append_env=True,
    )

    fx_rates = BashOperator(
        task_id="fx_rates",
        bash_command=ingest_cmd("src.ingest.fx_rates"),
        env=PIPELINE_ENV,
        append_env=True,
    )

    verify_load = BashOperator(
        task_id="verify_load",
        bash_command=ingest_cmd("src.ingest.verify_load"),
        env=PIPELINE_ENV,
        append_env=True,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=dbt_cmd("deps"),
    )

    # Staging (views) first: the snapshot reads them, and they must exist on
    # a fresh warehouse before anything downstream can compile.
    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=dbt_cmd("run --target prod --select staging"),
    )

    # SCD2 snapshot of the product catalogue (source of dim_products). Taken
    # every run so re-categorised/re-measured products spawn a new version.
    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=dbt_cmd("snapshot --target prod"),
    )

    # Everything that isn't staging: ephemeral intermediates (inlined) + the
    # mart tables, including dim_products now that the snapshot exists.
    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=dbt_cmd("run --target prod --exclude staging"),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=dbt_cmd("test --target prod"),
    )

    (
        [load_olist, fx_rates]
        >> verify_load
        >> dbt_deps
        >> dbt_run_staging
        >> dbt_snapshot
        >> dbt_run_marts
        >> dbt_test
    )
