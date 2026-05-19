"""Snowflake backend for the Olist ingest (week 2).

Bulk-loads via `snowflake.connector.pandas_tools.write_pandas`, which
internally PUTs the dataframe to an internal stage and runs COPY INTO
in chunks. Equivalent in spirit to Postgres COPY but using Snowflake's
native bulk-load path.

Identifiers are stored uppercase (Snowflake's default for unquoted
names); `count_tables` lowercases them on the way out so the manifest
in `src.ingest.expected` can stay canonical lowercase.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector import SnowflakeConnection
from snowflake.connector.pandas_tools import write_pandas

from src.ingest.config import load_env


def _env() -> dict[str, str]:
    load_env()
    return {
        "account":   os.environ["SNOWFLAKE_ACCOUNT"],
        "user":      os.environ["SNOWFLAKE_USER"],
        "password":  os.environ["SNOWFLAKE_PASSWORD"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database":  os.environ["SNOWFLAKE_DATABASE"],
        "schema":    os.environ["SNOWFLAKE_SCHEMA"],
        "role":      os.environ["SNOWFLAKE_ROLE"],
    }


def connect() -> SnowflakeConnection:
    return snowflake.connector.connect(**_env())


def bootstrap_schema(conn: SnowflakeConnection) -> None:
    cfg = _env()
    db, schema = cfg["database"], cfg["schema"]
    cur = conn.cursor()
    try:
        cur.execute(f'CREATE DATABASE IF NOT EXISTS "{db}"')
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{db}"."{schema}"')
        cur.execute(f'USE DATABASE "{db}"')
        cur.execute(f'USE SCHEMA "{schema}"')
    finally:
        cur.close()


def load_dataframe(
    conn: SnowflakeConnection, df: pd.DataFrame, table: str
) -> tuple[int, float]:
    """Drop-and-replace `<DB>.<SCHEMA>.<TABLE>` (uppercased) with `df`,
    bulk-loaded via `write_pandas` (internal stage + `COPY INTO`)."""
    t0 = time.perf_counter()
    success, _nchunks, nrows, _output = write_pandas(
        conn=conn,
        df=df,
        table_name=table.upper(),
        auto_create_table=True,
        overwrite=True,
        quote_identifiers=False,
    )
    if not success:
        raise RuntimeError(f"write_pandas reported failure for {table!r}")
    return nrows, time.perf_counter() - t0


def load_one(conn: SnowflakeConnection, csv_path: Path, table: str) -> tuple[int, float]:
    return load_dataframe(conn, pd.read_csv(csv_path), table)


def count_tables(conn: SnowflakeConnection) -> dict[str, int]:
    cfg = _env()
    db, schema = cfg["database"], cfg["schema"]
    counts: dict[str, int] = {}
    cur = conn.cursor()
    try:
        cur.execute(
            f'SELECT table_name FROM "{db}".INFORMATION_SCHEMA.TABLES '
            f"WHERE table_schema = %s ORDER BY table_name",
            (schema.upper(),),
        )
        tables = [r[0] for r in cur.fetchall()]
        for t in tables:
            cur.execute(f'SELECT count(*) FROM "{db}"."{schema}"."{t}"')
            counts[t.lower()] = int(cur.fetchone()[0])
    finally:
        cur.close()
    return counts


def close(conn: SnowflakeConnection) -> None:
    conn.close()
