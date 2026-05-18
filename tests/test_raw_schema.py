"""Integration test: the loaded Postgres raw schema must match the manifest.

Requires Postgres running and the load already executed:
    docker compose up -d
    python -m src.ingest.load_olist

Run with:
    pytest -m integration
"""

import pytest

from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.load_olist import build_engine
from src.ingest.verify_load import diff_counts, get_actual_counts


@pytest.mark.integration
def test_raw_schema_matches_expected_counts():
    engine = build_engine()
    actual = get_actual_counts(engine)
    problems = diff_counts(EXPECTED_ROW_COUNTS, actual)
    assert not problems, "row-count drift detected:\n" + "\n".join(problems)
