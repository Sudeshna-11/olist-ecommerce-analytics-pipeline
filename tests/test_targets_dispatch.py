"""Tests for the TARGET env-var dispatch (`src.ingest.targets.get_target`)."""

import pytest

from src.ingest.targets import VALID_TARGETS, get_target


def test_default_target_is_postgres(monkeypatch):
    monkeypatch.delenv("TARGET", raising=False)
    target = get_target()
    assert target.__name__.endswith(".postgres")


@pytest.mark.parametrize("name", VALID_TARGETS)
def test_named_targets_resolve(monkeypatch, name):
    monkeypatch.setenv("TARGET", name)
    target = get_target()
    assert target.__name__.endswith(f".{name}")


def test_target_name_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("TARGET", "SNOWFLAKE")
    assert get_target().__name__.endswith(".snowflake")


def test_unknown_target_raises(monkeypatch):
    monkeypatch.setenv("TARGET", "redshift")
    with pytest.raises(ValueError, match="Unknown TARGET"):
        get_target()


def test_targets_expose_required_interface():
    """Every backend must implement the same six-function protocol."""
    import importlib

    required = {
        "connect", "bootstrap_schema",
        "load_one", "load_dataframe",
        "count_tables", "close",
    }
    for name in VALID_TARGETS:
        mod = importlib.import_module(f"src.ingest.targets.{name}")
        missing = required - set(dir(mod))
        assert not missing, f"{name}: missing {missing}"
