"""Great Expectations source-data gate for the raw (bronze) Olist tables.

This validates the *raw* layer right after ingestion and before dbt runs - an
independent source-data contract. It deliberately complements, rather than
duplicates, the dbt tests: dbt guards the modelled staging/marts layers, while
this asserts what we expect of the source data itself (key integrity, value
domains, sane ranges). If a future Kaggle re-pull or upstream change violated
one of these, we'd catch it at the door instead of debugging a downstream mart.

Reads each raw table from Postgres via the same target engine the loader uses,
runs an in-code expectation suite per table with an ephemeral GX context, prints
a per-table summary, and exits non-zero if any expectation fails.

    TARGET=postgres python scripts/ge_validate.py

Runs against whatever the POSTGRES_* env points at - the full warehouse locally,
or the committed sample in CI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Keep the run hermetic and the CI log clean: no analytics callout, no tqdm bars.
os.environ.setdefault("GX_ANALYTICS_ENABLED", "false")
os.environ.setdefault("TQDM_DISABLE", "1")

import great_expectations as gx  # noqa: E402
import great_expectations.expectations as gxe  # noqa: E402
import pandas as pd  # noqa: E402

from src.ingest.config import load_env  # noqa: E402
from src.ingest.targets.postgres import RAW_SCHEMA, connect  # noqa: E402

# Brazilian order-status and payment-type domains (Olist's documented values).
ORDER_STATUSES = [
    "delivered", "shipped", "canceled", "unavailable",
    "invoiced", "processing", "created", "approved",
]
PAYMENT_TYPES = ["credit_card", "boleto", "voucher", "debit_card", "not_defined"]

# One suite per raw table. Each entry: list of GX expectations describing the
# source contract for that table.
SUITES: dict[str, list] = {
    "raw_orders": [
        gxe.ExpectTableRowCountToBeBetween(min_value=1),
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeUnique(column="order_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToBeInSet(column="order_status", value_set=ORDER_STATUSES),
        gxe.ExpectColumnValuesToNotBeNull(column="order_purchase_timestamp"),
    ],
    "raw_order_items": [
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="product_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="seller_id"),
        gxe.ExpectColumnValuesToBeBetween(column="price", min_value=0),
        gxe.ExpectColumnValuesToBeBetween(column="freight_value", min_value=0),
    ],
    "raw_order_payments": [
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeInSet(column="payment_type", value_set=PAYMENT_TYPES),
        gxe.ExpectColumnValuesToBeBetween(column="payment_value", min_value=0),
        gxe.ExpectColumnValuesToBeBetween(column="payment_installments", min_value=0),
    ],
    "raw_order_reviews": [
        gxe.ExpectColumnValuesToNotBeNull(column="review_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeBetween(column="review_score", min_value=1, max_value=5),
    ],
    "raw_customers": [
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToBeUnique(column="customer_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="customer_unique_id"),
        gxe.ExpectColumnValueLengthsToEqual(column="customer_state", value=2),
    ],
    "raw_products": [
        gxe.ExpectColumnValuesToNotBeNull(column="product_id"),
        gxe.ExpectColumnValuesToBeUnique(column="product_id"),
    ],
    "raw_sellers": [
        gxe.ExpectColumnValuesToNotBeNull(column="seller_id"),
        gxe.ExpectColumnValuesToBeUnique(column="seller_id"),
        gxe.ExpectColumnValueLengthsToEqual(column="seller_state", value=2),
    ],
    "raw_category_translation": [
        gxe.ExpectColumnValuesToNotBeNull(column="product_category_name"),
        gxe.ExpectColumnValuesToBeUnique(column="product_category_name"),
        gxe.ExpectColumnValuesToNotBeNull(column="product_category_name_english"),
    ],
    "raw_geolocation": [
        gxe.ExpectColumnValuesToNotBeNull(column="geolocation_zip_code_prefix"),
        gxe.ExpectColumnValuesToBeBetween(column="geolocation_lat", min_value=-90, max_value=90),
        gxe.ExpectColumnValuesToBeBetween(column="geolocation_lng", min_value=-180, max_value=180),
    ],
    "raw_fx_rates": [
        gxe.ExpectColumnValuesToNotBeNull(column="rate_date"),
        gxe.ExpectColumnValuesToBeInSet(column="base_currency", value_set=["BRL"]),
        gxe.ExpectColumnValuesToBeInSet(column="quote_currency", value_set=["USD", "EUR"]),
        gxe.ExpectColumnValuesToBeBetween(column="rate", min_value=0, strict_min=True),
    ],
}


def main() -> int:
    load_env()
    engine = connect()
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas("olist_raw")

    total_failures = 0
    print(f"Great Expectations source gate - schema '{RAW_SCHEMA}'\n")
    for table, expectations in SUITES.items():
        df = pd.read_sql_table(table, engine, schema=RAW_SCHEMA)
        asset = source.add_dataframe_asset(name=table)
        batch_def = asset.add_batch_definition_whole_dataframe(f"{table}_batch")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})

        suite = gx.ExpectationSuite(name=f"{table}_contract")
        for exp in expectations:
            suite.add_expectation(exp)
        result = batch.validate(suite)

        n = len(result.results)
        passed = sum(1 for r in result.results if r.success)
        flag = "OK  " if result.success else "FAIL"
        print(f"  [{flag}] {table:<26} {passed}/{n} expectations ({len(df):,} rows)")
        if not result.success:
            for r in result.results:
                if not r.success:
                    cfg = r.expectation_config
                    unexpected = dict(r.result).get("unexpected_count", "?")
                    print(f"         - {cfg.type} {cfg.kwargs} -> {unexpected} unexpected")
            total_failures += 1

    engine.dispose()
    print()
    if total_failures:
        print(f"Source gate FAILED: {total_failures} table(s) with violations.")
        return 1
    print(f"Source gate PASSED: all {len(SUITES)} raw tables meet their contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
