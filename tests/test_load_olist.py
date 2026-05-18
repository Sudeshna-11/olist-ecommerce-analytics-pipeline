"""Unit tests for the loader's pure logic — no database required."""

from src.ingest.load_olist import TABLE_MAP, build_engine


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


def test_build_engine_uses_postgres_env_vars(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "5499")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    engine = build_engine()
    url = engine.url

    assert url.drivername == "postgresql+psycopg2"
    assert url.username == "test_user"
    assert url.password == "test_pass"
    assert url.host == "db.example.com"
    assert url.port == 5499
    assert url.database == "test_db"
