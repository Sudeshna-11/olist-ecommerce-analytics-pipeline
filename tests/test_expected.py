"""Manifest-consistency tests for EXPECTED_ROW_COUNTS.

Sources of `raw_*` tables:
  - CSV-sourced (TABLE_MAP -> src.ingest.load_olist)
  - API-sourced (raw_fx_rates -> src.ingest.fx_rates)
"""

from src.ingest.expected import EXPECTED_ROW_COUNTS
from src.ingest.fx_rates import FX_TABLE
from src.ingest.load_olist import TABLE_MAP


def test_every_csv_destination_has_expected_count():
    """If load_olist writes a table, the manifest must say how many rows we expect."""
    destinations = set(TABLE_MAP.values())
    expected = set(EXPECTED_ROW_COUNTS)
    missing = destinations - expected
    assert not missing, f"CSV-sourced tables missing from manifest: {sorted(missing)}"


def test_no_orphan_expected_tables():
    """Every table in the manifest must be loaded by some known ingest."""
    valid_destinations = set(TABLE_MAP.values()) | {FX_TABLE}
    orphans = set(EXPECTED_ROW_COUNTS) - valid_destinations
    assert not orphans, f"manifest has orphan tables (nothing loads them): {sorted(orphans)}"


def test_expected_counts_are_positive_integers():
    for table, n in EXPECTED_ROW_COUNTS.items():
        assert isinstance(n, int) and n > 0, f"{table}: bad count {n!r}"
