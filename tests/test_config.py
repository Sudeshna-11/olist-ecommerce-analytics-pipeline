"""Tests for the dual-file env loader."""

from unittest.mock import patch

from src.ingest import config


def test_load_env_calls_both_files_in_order():
    with patch("src.ingest.config.load_dotenv") as mock:
        config.load_env()
    assert mock.call_count == 2
    first_call_path = mock.call_args_list[0].args[0]
    second_call_path = mock.call_args_list[1].args[0]
    assert first_call_path == config.ENV_FILE
    assert second_call_path == config.SECRETS_FILE


def test_secrets_file_loaded_with_override_true():
    """Secret values must win over anything in .env so a stale password
    in .env can't silently shadow the real one in .secrets.env."""
    with patch("src.ingest.config.load_dotenv") as mock:
        config.load_env()
    assert mock.call_args_list[1].kwargs.get("override") is True


def test_env_file_loaded_with_override_false():
    with patch("src.ingest.config.load_dotenv") as mock:
        config.load_env()
    first_kwargs = mock.call_args_list[0].kwargs
    assert first_kwargs.get("override") is False
