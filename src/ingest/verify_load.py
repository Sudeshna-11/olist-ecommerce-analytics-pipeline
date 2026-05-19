"""Verify the raw Olist load by comparing row counts to expected.

Reads the TARGET env var to decide which backend to query (same dispatch
as `load_olist`). Run after the load:

    python -m src.ingest.verify_load

Exits 0 if every expected table matches and no unexpected tables exist
in the raw schema. Exits 1 (and logs the diff) on any discrepancy.
"""

from __future__ import annotations

import logging
import sys

from src.ingest.config import load_env
from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.targets import get_target

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("snowflake").setLevel(logging.WARNING)
log = logging.getLogger("verify_load")


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
    load_env()

    target = get_target()
    log.info("Target backend: %s", target.__name__.rsplit(".", 1)[-1])

    conn = target.connect()
    try:
        actual = target.count_tables(conn)
    finally:
        target.close(conn)

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
