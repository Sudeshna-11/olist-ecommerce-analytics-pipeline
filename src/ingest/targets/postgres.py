"""Postgres backend for the Olist ingest (week 1 default).

Bulk-loads via psycopg2 COPY against a StringIO buffer. Pandas drives
column-type inference; an empty table is created with that schema, then
rows are streamed in via COPY.
"""

from __future__ import annotations

import io
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_SCHEMA = "raw"


def connect() -> Engine:
    load_dotenv(PROJECT_ROOT / ".env")
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, future=True)


def bootstrap_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}"))


def load_one(engine: Engine, csv_path: Path, table: str) -> tuple[int, float]:
    t0 = time.perf_counter()
    df = pd.read_csv(csv_path)

    df.head(0).to_sql(
        table,
        engine,
        schema=RAW_SCHEMA,
        if_exists="replace",
        index=False,
    )

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(
                f'COPY {RAW_SCHEMA}."{table}" FROM STDIN WITH (FORMAT CSV)',
                buf,
            )
        raw_conn.commit()
    finally:
        raw_conn.close()

    return len(df), time.perf_counter() - t0


def count_tables(engine: Engine) -> dict[str, int]:
    list_sql = text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = :schema ORDER BY table_name"
    )
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        tables = [row[0] for row in conn.execute(list_sql, {"schema": RAW_SCHEMA})]
        for t in tables:
            n = conn.execute(text(f'SELECT count(*) FROM {RAW_SCHEMA}."{t}"')).scalar_one()
            counts[t] = int(n)
    return counts


def close(engine: Engine) -> None:
    engine.dispose()
