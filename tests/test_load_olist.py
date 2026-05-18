"""Unit tests for the orchestrator's static shape - no database required."""

from src.ingest.load_olist import TABLE_MAP


def test_table_map_has_nine_sources():
    assert len(TABLE_MAP) == 9


def test_table_map_destinations_are_unique():
    destinations = list(TABLE_MAP.values())
    assert len(destinations) == len(set(destinations))


def test_table_map_destinations_use_raw_prefix():
    for src, dest in TABLE_MAP.items():
        assert dest.startswith("raw_"), f"{src} -> {dest} does not start with 'raw_'"


def test_table_map_sources_are_csvs():
    for src in TABLE_MAP:
        assert src.endswith(".csv"), f"source {src!r} is not a .csv"
