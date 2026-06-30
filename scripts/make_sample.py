"""Carve a small, referentially-consistent sample out of the full Olist CSVs.

CI cannot use the real Kaggle CSVs (they're gitignored and need credentials to
download), so the integration job runs the full ingest -> dbt -> Great
Expectations pipeline against a committed *sample* instead. For that sample to
survive dbt's relationship/uniqueness tests, it must be a closed slice of the
foreign-key graph: every child row's parent must also be present.

Carving order (parents pulled in to cover every child that survives):

    orders            <- random sample of N order_ids (the seed set)
      customers       <- the customer_id behind each sampled order
      order_items     <- items for sampled orders -> product_ids, seller_ids
        products      <- products referenced by those items
        sellers       <- sellers referenced by those items
      order_payments  <- payments for sampled orders
      order_reviews   <- reviews for sampled orders
      geolocation     <- rows for every zip prefix used by a kept customer/seller
    category_translation  <- kept whole (71 rows; tiny, and dim_products needs it)

FX rates are fetched for the full default range (same as production) so the
forward-fill in dbt always covers the sampled order dates, and written out as a
CSV for hermetic, offline loading in CI (no Frankfurter call on the runner).

This is a developer tool: run it once locally (where the real CSVs live) and
commit the result under tests/fixtures/sample_raw/.

    python scripts/make_sample.py --orders 500
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.ingest.fx_rates import (  # noqa: E402
    BASE_CURRENCY,
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    QUOTE_CURRENCIES,
    fetch_rates,
)
from src.ingest.load_olist import TABLE_MAP  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_DIR = REPO_ROOT / "tests" / "fixtures" / "sample_raw"
FX_CSV_NAME = "olist_fx_rates_sample.csv"
MANIFEST_NAME = "_manifest.json"
SEED = 42


def _read(name: str) -> pd.DataFrame:
    # utf-8-sig strips the BOM on product_category_name_translation.csv.
    return pd.read_csv(RAW_DIR / name, encoding="utf-8-sig", dtype=str)


def build_sample(n_orders: int, geo_per_zip: int) -> dict[str, pd.DataFrame]:
    orders = _read("olist_orders_dataset.csv")
    items = _read("olist_order_items_dataset.csv")
    payments = _read("olist_order_payments_dataset.csv")
    reviews = _read("olist_order_reviews_dataset.csv")
    customers = _read("olist_customers_dataset.csv")
    products = _read("olist_products_dataset.csv")
    sellers = _read("olist_sellers_dataset.csv")
    geo = _read("olist_geolocation_dataset.csv")
    category = _read("product_category_name_translation.csv")

    # Seed set: a deterministic random sample of orders.
    sample_orders = orders.sample(
        n=min(n_orders, len(orders)), random_state=SEED
    ).sort_values("order_purchase_timestamp")
    order_ids = set(sample_orders["order_id"])

    sample_items = items[items["order_id"].isin(order_ids)]
    sample_payments = payments[payments["order_id"].isin(order_ids)]
    sample_reviews = reviews[reviews["order_id"].isin(order_ids)]

    customer_ids = set(sample_orders["customer_id"])
    sample_customers = customers[customers["customer_id"].isin(customer_ids)]

    product_ids = set(sample_items["product_id"].dropna())
    sample_products = products[products["product_id"].isin(product_ids)]

    seller_ids = set(sample_items["seller_id"].dropna())
    sample_sellers = sellers[sellers["seller_id"].isin(seller_ids)]

    # Geolocation is keyed by zip prefix; keep every row for the prefixes that a
    # kept customer or seller points at. Missing prefixes are fine (dim_* left
    # join geo, so unmatched rows just get null lat/lng) but covering them keeps
    # the centroid join faithful.
    zips = set(sample_customers["customer_zip_code_prefix"].dropna()) | set(
        sample_sellers["seller_zip_code_prefix"].dropna()
    )
    sample_geo = (
        geo[geo["geolocation_zip_code_prefix"].isin(zips)]
        .groupby("geolocation_zip_code_prefix", sort=False)
        .head(geo_per_zip)
    )

    # filename (matching TABLE_MAP keys) -> frame
    return {
        "olist_orders_dataset.csv": sample_orders,
        "olist_order_items_dataset.csv": sample_items,
        "olist_order_payments_dataset.csv": sample_payments,
        "olist_order_reviews_dataset.csv": sample_reviews,
        "olist_customers_dataset.csv": sample_customers,
        "olist_products_dataset.csv": sample_products,
        "olist_sellers_dataset.csv": sample_sellers,
        "olist_geolocation_dataset.csv": sample_geo,
        "product_category_name_translation.csv": category,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--orders", type=int, default=500, help="seed order count")
    ap.add_argument(
        "--geo-per-zip",
        type=int,
        default=3,
        help="max geolocation rows kept per zip prefix (centroid is an average, "
        "so a few points per prefix reproduce the join faithfully while keeping "
        "the committed fixture small)",
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = build_sample(args.orders, args.geo_per_zip)

    manifest: dict[str, int] = {}
    print(f"Writing sample ({args.orders} seed orders) -> {OUT_DIR}")
    for filename, df in frames.items():
        df.to_csv(OUT_DIR / filename, index=False)
        table = TABLE_MAP[filename]
        manifest[table] = len(df)
        print(f"  {filename:<44} {len(df):>7,} rows -> {table}")

    # FX rates: full production range, written as a CSV for offline CI loading.
    fx = fetch_rates(DEFAULT_START_DATE, DEFAULT_END_DATE, BASE_CURRENCY, QUOTE_CURRENCIES)
    fx.to_csv(OUT_DIR / FX_CSV_NAME, index=False)
    manifest["raw_fx_rates"] = len(fx)
    print(f"  {FX_CSV_NAME:<44} {len(fx):>7,} rows -> raw_fx_rates")

    (OUT_DIR / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  {MANIFEST_NAME:<44} {len(manifest)} tables")
    print(f"Total raw rows in sample: {sum(manifest.values()):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
