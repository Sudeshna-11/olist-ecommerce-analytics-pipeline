"""Load raw Olist CSV files into the configured warehouse.

Expects all 9 Olist CSVs in `data/raw/`. Loads each one as a 1:1 table
into the bronze (`raw`) schema with no transformation - that's dbt's job
later.

The target backend is selected by the TARGET env var:
  - TARGET=postgres  (default, week 1)
  - TARGET=snowflake (week 2+)

Run with:   python -m src.ingest.load_olist
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.ingest.targets import get_target

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("snowflake").setLevel(logging.WARNING)
log = logging.getLogger("load_olist")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Source CSV -> destination table (canonical lowercase, bronze layer)
TABLE_MAP: dict[str, str] = {
    "olist_customers_dataset.csv":             "raw_customers",
    "olist_geolocation_dataset.csv":           "raw_geolocation",
    "olist_order_items_dataset.csv":           "raw_order_items",
    "olist_order_payments_dataset.csv":        "raw_order_payments",
    "olist_order_reviews_dataset.csv":         "raw_order_reviews",
    "olist_orders_dataset.csv":                "raw_orders",
    "olist_products_dataset.csv":              "raw_products",
    "olist_sellers_dataset.csv":               "raw_sellers",
    "product_category_name_translation.csv":   "raw_category_translation",
}


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    missing = [f for f in TABLE_MAP if not (RAW_DIR / f).exists()]
    if missing:
        log.error("Missing %d CSV file(s) in %s:", len(missing), RAW_DIR)
        for f in missing:
            log.error("  - %s", f)
        log.error("See data/README.md for how to download them.")
        sys.exit(1)

    target = get_target()
    log.info("Target backend: %s", target.__name__.rsplit(".", 1)[-1])

    conn = target.connect()
    try:
        target.bootstrap_schema(conn)

        total_rows = 0
        total_secs = 0.0
        for filename, table in TABLE_MAP.items():
            log.info("Loading %-44s -> %s", filename, table)
            n, secs = target.load_one(conn, RAW_DIR / filename, table)
            rate = int(n / secs) if secs > 0 else 0
            log.info("  %s rows in %5.1fs (%s rows/s)", f"{n:>9,}", secs, f"{rate:,}")
            total_rows += n
            total_secs += secs

        log.info(
            "Done. %s rows across %d tables in %.1fs.",
            f"{total_rows:,}",
            len(TABLE_MAP),
            total_secs,
        )
    finally:
        target.close(conn)


if __name__ == "__main__":
    main()
