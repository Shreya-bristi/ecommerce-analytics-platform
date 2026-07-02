"""
EXTRACT: Read raw CSVs and load into ecom_staging tables.
Idempotent: safe to re-run (TRUNCATE + INSERT).
"""
import pandas as pd
from config import get_engine
from sqlalchemy import text

DATA_DIR = "../data/raw"

FILE_TABLE_MAP = {
    "olist_orders_dataset.csv":        "stg_orders",
    "olist_order_items_dataset.csv":   "stg_order_items",
    "olist_customers_dataset.csv":     "stg_customers",
    "olist_products_dataset.csv":      "stg_products",
    "olist_order_payments_dataset.csv":"stg_payments",
    "product_category_name_translation.csv": "stg_category_translation",
}

def extract_all():
    engine = get_engine("ecom_staging")

    for csv_file, table_name in FILE_TABLE_MAP.items():
        print(f"  Loading {csv_file} → {table_name}...")
        df = pd.read_csv(f"{DATA_DIR}/{csv_file}")

        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))

        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"  ✓ {len(df):,} rows loaded")

if __name__ == "__main__":
    print("=== EXTRACT PHASE ===")
    extract_all()
    print("=== EXTRACT COMPLETE ===")