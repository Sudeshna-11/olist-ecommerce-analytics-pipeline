"""Fetch historical FX rates from Frankfurter and land in raw.raw_fx_rates.

The Olist dataset is denominated in BRL; downstream marts need to report
revenue in USD/EUR. We pull daily BRL->USD and BRL->EUR rates from
api.frankfurter.app (free, no API key, sourced from ECB daily reference
rates) for the date range bracketing the order timestamps, and land
them as a long-format table:

    rate_date | base_currency | quote_currency | rate
    ----------+---------------+----------------+----------
    2016-09-01| BRL           | EUR            | 0.27454
    2016-09-01| BRL           | USD            | 0.30721
    ...

Date range is configurable via FX_START_DATE / FX_END_DATE env vars;
defaults bracket the Olist order span.

Run with:   python -m src.ingest.fx_rates
"""

from __future__ import annotations

import logging
import os

import pandas as pd
import requests

from src.ingest.config import load_env
from src.ingest.targets import get_target

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("snowflake").setLevel(logging.WARNING)
log = logging.getLogger("fx_rates")

DEFAULT_START_DATE = "2016-09-01"   # Olist's first order is 2016-09-15
DEFAULT_END_DATE = "2018-12-31"     # buffers past Olist's last order (2018-10)
BASE_CURRENCY = "BRL"
QUOTE_CURRENCIES = ("USD", "EUR")
API_URL_TEMPLATE = "https://api.frankfurter.app/{start}..{end}"
FX_TABLE = "raw_fx_rates"


def fetch_rates(
    start_date: str,
    end_date: str,
    base: str,
    quotes: tuple[str, ...],
) -> pd.DataFrame:
    """Hit Frankfurter for a date range and return a long-format dataframe."""
    url = API_URL_TEMPLATE.format(start=start_date, end=end_date)
    params = {"from": base, "to": ",".join(quotes)}
    log.info("GET %s  from=%s to=%s", url, base, ",".join(quotes))

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    rows: list[dict] = []
    for date_str, currency_map in payload.get("rates", {}).items():
        for quote, rate in currency_map.items():
            rows.append({
                "rate_date": date_str,
                "base_currency": base,
                "quote_currency": quote,
                "rate": float(rate),
            })

    if not rows:
        raise RuntimeError(
            f"Frankfurter returned no rates for {base}->{quotes} "
            f"between {start_date} and {end_date}"
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["rate_date", "quote_currency"])
        .reset_index(drop=True)
    )


def main() -> None:
    load_env()

    # Offline mode: load a pre-fetched CSV instead of calling Frankfurter. Used
    # by the CI integration job so the run stays hermetic (no external network
    # dependency). The CSV is the long-format output of fetch_rates().
    csv_path = os.environ.get("FX_RATES_CSV")
    if csv_path:
        df = pd.read_csv(csv_path)
        log.info("Loaded %s FX rows from %s (offline mode)", f"{len(df):,}", csv_path)
    else:
        start = os.environ.get("FX_START_DATE", DEFAULT_START_DATE)
        end = os.environ.get("FX_END_DATE", DEFAULT_END_DATE)
        df = fetch_rates(start, end, BASE_CURRENCY, QUOTE_CURRENCIES)
        log.info(
            "Fetched %s rows (%s..%s, %s -> %s)",
            f"{len(df):,}", start, end, BASE_CURRENCY, ",".join(QUOTE_CURRENCIES),
        )

    target = get_target()
    log.info("Target backend: %s", target.__name__.rsplit(".", 1)[-1])

    conn = target.connect()
    try:
        target.bootstrap_schema(conn)
        n, secs = target.load_dataframe(conn, df, FX_TABLE)
        log.info("Loaded %s: %s rows in %.1fs", FX_TABLE, f"{n:,}", secs)
    finally:
        target.close(conn)


if __name__ == "__main__":
    main()
