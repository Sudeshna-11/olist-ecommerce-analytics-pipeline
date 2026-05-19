"""Integration test: the loaded raw schema must match the manifest.

Loads `.env` + `.secrets.env` so the configured TARGET takes effect.
Requires both ingest scripts to have already run:

    python -m src.ingest.load_olist
    python -m src.ingest.fx_rates
    pytest -m integration
"""

import pytest

from src.ingest.config import load_env
from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.targets import get_target
from src.ingest.verify_load import diff_counts


@pytest.mark.integration
def test_raw_schema_matches_expected_counts():
    load_env()
    target = get_target()
    conn = target.connect()
    try:
        actual = target.count_tables(conn)
    finally:
        target.close(conn)
    problems = diff_counts(EXPECTED_ROW_COUNTS, actual)
    assert not problems, "row-count drift detected:\n" + "\n".join(problems)
