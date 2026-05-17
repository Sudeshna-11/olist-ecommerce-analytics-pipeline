# Data directory

Raw input data lives here. CSV files are **not** committed to git (see `.gitignore`); only this README and the `.gitkeep` are.

## Getting the Olist dataset

The pipeline expects 9 CSVs from the [Brazilian Olist e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) in `data/raw/`. Free Kaggle account required.

### Option A — Kaggle CLI (recommended)

```powershell
pip install kaggle

# Get an API token at https://www.kaggle.com/settings -> "Create New API Token"
# Save the downloaded kaggle.json to %USERPROFILE%\.kaggle\kaggle.json

kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

### Option B — Manual download

1. Visit https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Click **Download** (~45 MB zip)
3. Extract all 9 CSVs into `data/raw/`

## Files expected in `data/raw/`

| File | Rows (approx) | What's in it |
|---|---|---|
| `olist_customers_dataset.csv` | 99,441 | Customer IDs + ZIP-level location |
| `olist_geolocation_dataset.csv` | 1,000,163 | ZIP code → lat/lng |
| `olist_order_items_dataset.csv` | 112,650 | Line items per order |
| `olist_order_payments_dataset.csv` | 103,886 | Payment methods + amounts |
| `olist_order_reviews_dataset.csv` | 99,224 | 1–5 star reviews + comments |
| `olist_orders_dataset.csv` | 99,441 | Order header + timestamps |
| `olist_products_dataset.csv` | 32,951 | Product attributes |
| `olist_sellers_dataset.csv` | 3,095 | Seller IDs + location |
| `product_category_name_translation.csv` | 71 | Portuguese → English category names |
