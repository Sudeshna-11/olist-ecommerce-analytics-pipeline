"""Manifest-consistency tests: the expected-counts dict must stay in sync with TABLE_MAP."""

from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.load_olist import TABLE_MAP


def test_expected_counts_cover_every_loader_destination():
    destinations = set(TABLE_MAP.values())
    expected_tables = set(EXPECTED_ROW_COUNTS)
    assert destinations == expected_tables, (
        f"loader writes tables with no expected count: {sorted(destinations - expected_tables)}; "
        f"manifest has orphan tables: {sorted(expected_tables - destinations)}"
    )


def test_expected_counts_are_positive_integers():
    for table, n in EXPECTED_ROW_COUNTS.items():
        assert isinstance(n, int) and n > 0, f"{table}: bad count {n!r}"
