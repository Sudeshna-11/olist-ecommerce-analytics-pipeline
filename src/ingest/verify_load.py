"""Verify the raw Olist load by comparing row counts to expected.

Run after `python -m src.ingest.load_olist`:

    python -m src.ingest.verify_load

Exits 0 if every expected table matches and no unexpected tables exist
in the raw schema. Exits 1 (and logs the diff) on any discrepancy.
"""

from __future__ import annotations

import logging
import sys

from sqlalchemy import Engine, text

from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.load_olist import build_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("verify_load")


def get_actual_counts(engine: Engine) -> dict[str, int]:
    """Return {table_name: row_count} for every table in the raw schema."""
    list_sql = text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'raw' ORDER BY table_name"
    )
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        tables = [row[0] for row in conn.execute(list_sql)]
        for table in tables:
            n = conn.execute(text(f'SELECT count(*) FROM raw."{table}"')).scalar_one()
            counts[table] = int(n)
    return counts


def diff_counts(expected: dict[str, int], actual: dict[str, int]) -> list[str]:
    """Return human-readable mismatch lines; empty list means clean."""
    problems: list[str] = []
    for table, exp in expected.items():
        if table not in actual:
            problems.append(f"  - {table}: MISSING (expected {exp:,} rows)")
        elif actual[table] != exp:
            delta = actual[table] - exp
            problems.append(
                f"  - {table}: expected {exp:,}, got {actual[table]:,} "
                f"(delta {delta:+,})"
            )
    for table in sorted(set(actual) - set(expected)):
        problems.append(
            f"  - {table}: UNEXPECTED table in raw schema ({actual[table]:,} rows)"
        )
    return problems


def main() -> int:
    engine = build_engine()
    actual = get_actual_counts(engine)
    problems = diff_counts(EXPECTED_ROW_COUNTS, actual)

    if problems:
        log.error("Row-count check FAILED (%d issue(s)):", len(problems))
        for line in problems:
            log.error(line)
        return 1

    total = sum(EXPECTED_ROW_COUNTS.values())
    log.info(
        "OK - all %d tables match expected counts (%s rows total).",
        len(EXPECTED_ROW_COUNTS),
        f"{total:,}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
