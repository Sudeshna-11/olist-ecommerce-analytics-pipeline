"""Unit tests for the Snowflake target - connector is mocked, no network calls."""

from unittest.mock import patch


def _set_snowflake_env(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-account")
    monkeypatch.setenv("SNOWFLAKE_USER", "test_user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test_pass")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "TEST_WH")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "TEST_DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "RAW")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "TEST_ROLE")


def test_connect_passes_all_env_vars_to_connector(monkeypatch):
    _set_snowflake_env(monkeypatch)

    with patch("snowflake.connector.connect") as mock_connect:
        mock_connect.return_value = "fake-conn"
        from src.ingest.targets import snowflake

        result = snowflake.connect()

    assert result == "fake-conn"
    mock_connect.assert_called_once_with(
        account="test-account",
        user="test_user",
        password="test_pass",
        warehouse="TEST_WH",
        database="TEST_DB",
        schema="RAW",
        role="TEST_ROLE",
    )


def test_bootstrap_schema_creates_db_and_schema(monkeypatch):
    _set_snowflake_env(monkeypatch)
    from src.ingest.targets import snowflake

    fake_cursor = type(
        "Cur",
        (),
        {
            "execute": lambda self, sql, *a: self._calls.append(sql),
            "close": lambda self: None,
        },
    )()
    fake_cursor._calls = []
    fake_conn = type("Conn", (), {"cursor": lambda self: fake_cursor})()

    snowflake.bootstrap_schema(fake_conn)

    joined = "\n".join(fake_cursor._calls)
    assert 'CREATE DATABASE IF NOT EXISTS "TEST_DB"' in joined
    assert 'CREATE SCHEMA IF NOT EXISTS "TEST_DB"."RAW"' in joined
    assert 'USE DATABASE "TEST_DB"' in joined
    assert 'USE SCHEMA "RAW"' in joined


def test_load_one_uses_uppercase_table_name(monkeypatch):
    _set_snowflake_env(monkeypatch)

    captured: dict = {}

    def fake_write_pandas(*, conn, df, table_name, **kwargs):
        captured["table_name"] = table_name
        captured["kwargs"] = kwargs
        return True, 1, len(df), {}

    with patch("src.ingest.targets.snowflake.write_pandas", side_effect=fake_write_pandas), \
         patch("src.ingest.targets.snowflake.pd.read_csv", return_value=__import__("pandas").DataFrame({"a": [1, 2, 3]})):
        from src.ingest.targets import snowflake

        n, secs = snowflake.load_one(conn=object(), csv_path="dummy.csv", table="raw_customers")

    assert n == 3
    assert secs >= 0
    assert captured["table_name"] == "RAW_CUSTOMERS"
    assert captured["kwargs"]["auto_create_table"] is True
    assert captured["kwargs"]["overwrite"] is True
    assert captured["kwargs"]["quote_identifiers"] is False


def test_load_one_raises_on_write_pandas_failure(monkeypatch):
    _set_snowflake_env(monkeypatch)

    with patch("src.ingest.targets.snowflake.write_pandas", return_value=(False, 0, 0, {})), \
         patch("src.ingest.targets.snowflake.pd.read_csv", return_value=__import__("pandas").DataFrame({"a": [1]})):
        from src.ingest.targets import snowflake
        import pytest as _pytest

        with _pytest.raises(RuntimeError, match="write_pandas reported failure"):
            snowflake.load_one(conn=object(), csv_path="dummy.csv", table="raw_x")
