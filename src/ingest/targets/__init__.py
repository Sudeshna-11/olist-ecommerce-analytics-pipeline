"""Target backends for the Olist ingest.

Each backend module (postgres, snowflake) exposes the same four-function
interface:

    connect()                       -> Connection
    bootstrap_schema(conn)          -> None
    load_one(conn, csv_path, table) -> (row_count, elapsed_seconds)
    count_tables(conn)              -> {table_name (lowercased): row_count}
    close(conn)                     -> None

`get_target()` reads the TARGET env var (default: postgres) and returns
the matching module so callers can stay backend-agnostic.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

VALID_TARGETS = ("postgres", "snowflake")


def get_target() -> ModuleType:
    """Pure dispatch on os.environ['TARGET'] - call `load_env()` first if you
    want .env values respected."""
    name = (os.environ.get("TARGET") or "postgres").strip().lower()
    if name not in VALID_TARGETS:
        raise ValueError(
            f"Unknown TARGET={name!r}; must be one of {VALID_TARGETS}"
        )
    return importlib.import_module(f"src.ingest.targets.{name}")
