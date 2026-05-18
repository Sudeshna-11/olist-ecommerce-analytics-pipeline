"""Load raw Olist CSV files into Postgres.

Expects all 9 Olist CSVs in `data/raw/`. Loads each one as a 1:1 table
into the `raw` schema with no transformation — that's dbt's job later.

Run with:   python -m src.ingest.load_olist
"""

from __future__ import annotations

import io
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_olist")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Source CSV -> destination table
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


def build_engine():
    load_dotenv(PROJECT_ROOT / ".env")
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, future=True)


def load_one(engine, csv_path: Path, table: str) -> tuple[int, float]:
    """Load a CSV into `raw.<table>`. Returns (row_count, elapsed_seconds).

    Pandas infers the column types from the CSV; an empty table is created
    with that schema, then rows are bulk-loaded via Postgres COPY — roughly
    an order of magnitude faster than row-by-row INSERTs on the 1M-row
    geolocation file.
    """
    t0 = time.perf_counter()
    df = pd.read_csv(csv_path)

    df.head(0).to_sql(
        table,
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
    )

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(
                f'COPY raw."{table}" FROM STDIN WITH (FORMAT CSV)',
                buf,
            )
        raw_conn.commit()
    finally:
        raw_conn.close()

    return len(df), time.perf_counter() - t0


def main() -> None:
    missing = [f for f in TABLE_MAP if not (RAW_DIR / f).exists()]
    if missing:
        log.error("Missing %d CSV file(s) in %s:", len(missing), RAW_DIR)
        for f in missing:
            log.error("  - %s", f)
        log.error("See data/README.md for how to download them.")
        sys.exit(1)

    engine = build_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

    total_rows = 0
    total_secs = 0.0
    for filename, table in TABLE_MAP.items():
        log.info("Loading %-44s -> raw.%s", filename, table)
        n, secs = load_one(engine, RAW_DIR / filename, table)
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


if __name__ == "__main__":
    main()
