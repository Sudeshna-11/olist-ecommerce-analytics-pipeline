"""Unit tests for the Postgres target's pure logic."""

from src.ingest.targets.postgres import connect


def test_connect_builds_engine_from_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "5499")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    engine = connect()
    url = engine.url

    assert url.drivername == "postgresql+psycopg2"
    assert url.username == "test_user"
    assert url.password == "test_pass"
    assert url.host == "db.example.com"
    assert url.port == 5499
    assert url.database == "test_db"
