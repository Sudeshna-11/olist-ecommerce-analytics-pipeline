"""Tests for the FX rates fetcher - the Frankfurter API is mocked."""

from unittest.mock import MagicMock, patch

import pytest

from src.ingest.fx_rates import (
    BASE_CURRENCY,
    QUOTE_CURRENCIES,
    fetch_rates,
)


_FAKE_PAYLOAD = {
    "amount": 1.0,
    "base": "BRL",
    "start_date": "2017-01-02",
    "end_date": "2017-01-04",
    "rates": {
        "2017-01-02": {"USD": 0.3072, "EUR": 0.2932},
        "2017-01-03": {"USD": 0.3084, "EUR": 0.2940},
        "2017-01-04": {"USD": 0.3098, "EUR": 0.2951},
    },
}


def _fake_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_fetch_rates_flattens_payload_into_long_format():
    with patch("src.ingest.fx_rates.requests.get", return_value=_fake_response(_FAKE_PAYLOAD)):
        df = fetch_rates("2017-01-02", "2017-01-04", "BRL", ("USD", "EUR"))

    assert len(df) == 6  # 3 dates x 2 quote currencies
    assert set(df.columns) == {"rate_date", "base_currency", "quote_currency", "rate"}
    assert (df["base_currency"] == "BRL").all()
    assert set(df["quote_currency"]) == {"USD", "EUR"}


def test_fetch_rates_is_sorted_for_deterministic_load():
    with patch("src.ingest.fx_rates.requests.get", return_value=_fake_response(_FAKE_PAYLOAD)):
        df = fetch_rates("2017-01-02", "2017-01-04", "BRL", ("USD", "EUR"))

    dates = list(df["rate_date"])
    assert dates == sorted(dates)


def test_fetch_rates_passes_correct_api_params():
    captured = {}

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        return _fake_response(_FAKE_PAYLOAD)

    with patch("src.ingest.fx_rates.requests.get", side_effect=fake_get):
        fetch_rates("2017-01-02", "2017-01-04", "BRL", ("USD", "EUR"))

    assert captured["url"] == "https://api.frankfurter.app/2017-01-02..2017-01-04"
    assert captured["params"] == {"from": "BRL", "to": "USD,EUR"}


def test_fetch_rates_raises_on_empty_response():
    empty = {**_FAKE_PAYLOAD, "rates": {}}
    with patch("src.ingest.fx_rates.requests.get", return_value=_fake_response(empty)):
        with pytest.raises(RuntimeError, match="no rates"):
            fetch_rates("2017-01-02", "2017-01-04", "BRL", ("USD", "EUR"))


def test_constants_are_sensible():
    assert BASE_CURRENCY == "BRL"  # Olist is Brazilian
    assert "USD" in QUOTE_CURRENCIES
    assert "EUR" in QUOTE_CURRENCIES
