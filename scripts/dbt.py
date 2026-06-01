"""Wrapper around the dbt CLI that loads .env + .secrets.env first.

Usage examples (from repo root):
    python scripts/dbt.py debug
    python scripts/dbt.py deps
    python scripts/dbt.py run --select staging
    python scripts/dbt.py test
    python scripts/dbt.py run --target prod

Equivalent raw invocation (for reference / CI):
    DBT_PROFILES_DIR=olist_dbt dbt run --project-dir olist_dbt --select staging
The raw form requires the developer's shell to already have POSTGRES_*
and SNOWFLAKE_* env vars set; this wrapper does that step via the same
`load_env()` the ingest entry points use.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.ingest.config import load_env  # noqa: E402

PROJECT_DIR = REPO_ROOT / "olist_dbt"


def main() -> int:
    load_env()
    cmd = [
        "dbt",
        *sys.argv[1:],
        "--project-dir", str(PROJECT_DIR),
        "--profiles-dir", str(PROJECT_DIR),
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
