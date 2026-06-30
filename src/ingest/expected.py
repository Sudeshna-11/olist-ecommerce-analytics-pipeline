"""Expected row counts for the raw Olist tables.

The Olist Kaggle dataset is immutable, so these are static reference values.
Source: data/README.md, cross-checked against the loader output.

Used by:
  - src.ingest.verify_load  (post-load row-count check)
  - tests/                  (manifest-consistency tests)

For sampled loads (the CI integration job runs the pipeline against a small
referentially-consistent slice, not the full Kaggle dataset), set the
``OLIST_EXPECTED_COUNTS`` env var to a JSON file of ``{table: count}`` and
``load_expected_counts()`` returns that instead of the full-dataset constant.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

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
    # raw_fx_rates: 596 ECB business days * 2 quote currencies (USD, EUR)
    # over the default date range 2016-09-01..2018-12-31.
    "raw_fx_rates":                 1_192,
}

EXPECTED_COUNTS_ENV = "OLIST_EXPECTED_COUNTS"


def load_expected_counts() -> dict[str, int]:
    """Return the expected raw row counts.

    Defaults to the full-dataset constant. If ``OLIST_EXPECTED_COUNTS`` points
    at a JSON manifest (as the CI integration job does for the sample load),
    return that instead.
    """
    path = os.environ.get(EXPECTED_COUNTS_ENV)
    if not path:
        return dict(EXPECTED_ROW_COUNTS)
    data = json.loads(Path(path).read_text())
    return {table: int(count) for table, count in data.items()}
