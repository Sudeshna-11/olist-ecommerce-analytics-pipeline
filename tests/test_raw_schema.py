"""Integration test: the loaded raw schema must match the manifest.

Hits whichever backend TARGET points at (postgres by default). Requires
the load to have already been run:

    docker compose up -d            # if TARGET=postgres
    python -m src.ingest.load_olist
    pytest -m integration
"""

import pytest

from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.targets import get_target
from src.ingest.verify_load import diff_counts


@pytest.mark.integration
def test_raw_schema_matches_expected_counts():
    target = get_target()
    conn = target.connect()
    try:
        actual = target.count_tables(conn)
    finally:
        target.close(conn)
    problems = diff_counts(EXPECTED_ROW_COUNTS, actual)
    assert not problems, "row-count drift detected:\n" + "\n".join(problems)
