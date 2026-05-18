"""Expected row counts for the raw Olist tables.

The Olist Kaggle dataset is immutable, so these are static reference values.
Source: data/README.md, cross-checked against the loader output.

Used by:
  - src.ingest.verify_load  (post-load row-count check)
  - tests/                  (manifest-consistency tests)
"""

from __future__ import annotations

EXPECTED_ROW_COUNTS: dict[str, int] = {
    "raw_customers":               99_441,
    "raw_geolocation":          1_000_163,
    "raw_order_items":            112_650,
    "raw_order_payments":         103_886,
    "raw_order_reviews":           99_224,
    "raw_orders":                  99_441,
    "raw_products":                32_951,
    "raw_sellers":                  3_095,
    "raw_category_translation":        71,
}
