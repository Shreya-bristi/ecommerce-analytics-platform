"""
TRANSFORM: Read from ecom_staging, clean and normalise,
write to ecom_core tables. Handles deduplication, type casting,
surrogate key generation, and synthetic data enrichment
(sessions, campaigns, A/B test assignments).
"""
import pandas as pd
import numpy as np
import hashlib
from config import get_engine

def deterministic_variant(session_id: str, experiment: str) -> str:
    """Assign A/B variant deterministically using a hash.
    This ensures the same session always gets the same variant —
    critical for reproducible A/B testing."""
    h = hashlib.md5(f"{session_id}_{experiment}".encode()).hexdigest()
    return "variant" if int(h, 16) % 2 == 0 else "control"

def transform_categories(stg_engine, core_engine):
    """Load category translation, deduplicate, insert into categories."""
    df = pd.read_sql("SELECT * FROM stg_category_translation", stg_engine)
    df = df.drop_duplicates(subset=["product_category_name"])
    df = df.rename(columns={
        "product_category_name": "name_pt",
        "product_category_name_english": "name_en"
    })
    df.to_sql("categories", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df)} categories")
    return df

def transform_customers(stg_engine, core_engine):
    """Deduplicate customers by unique_id (take first occurrence)."""
    df = pd.read_sql("SELECT * FROM stg_customers", stg_engine)
    df = df.drop_duplicates(subset=["customer_unique_id"], keep="first")
    df = df.rename(columns={
        "customer_id": "source_id",
        "customer_unique_id": "unique_id",
        "customer_zip_code_prefix": "zip_code_prefix",
        "customer_city": "city",
        "customer_state": "state"
    })
    df["city"] = df["city"].str.title().str.strip()
    df.to_sql("customers", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} customers (deduped from {len(pd.read_sql('SELECT COUNT(*) FROM stg_customers', stg_engine).iloc[0,0]):,})")
    return df

def transform_products(stg_engine, core_engine):
    """Map products to category IDs, clean nulls."""
    products = pd.read_sql("SELECT * FROM stg_products", stg_engine)
    categories = pd.read_sql("SELECT category_id, name_pt FROM categories", core_engine)

    products = products.merge(
        categories,
        left_on="product_category_name",
        right_on="name_pt",
        how="left"
    )
    products = products.rename(columns={"product_id": "source_id"})
    products = products[["source_id", "category_id", "product_weight_g",
                         "product_length_cm", "product_height_cm", "product_width_cm"]]
    products.columns = ["source_id", "category_id", "weight_g",
                        "length_cm", "height_cm", "width_cm"]
    products.to_sql("products", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(products):,} products")
    return products

def transform_orders(stg_engine, core_engine):
    """Map orders to customer surrogate keys, parse dates, map status."""
    orders = pd.read_sql("SELECT * FROM stg_orders", stg_engine)
    customers = pd.read_sql("SELECT customer_id, source_id FROM customers", core_engine)

    orders = orders.merge(customers, left_on="customer_id", right_on="source_id", how="left")

    orders = orders.rename(columns={
        "order_id": "source_id",
        "customer_id_y": "customer_id",
        "order_status": "status",
        "order_purchase_timestamp": "ordered_at",
        "order_approved_at": "approved_at",
        "order_delivered_carrier_date": "delivered_carrier",
        "order_delivered_customer_date": "delivered_customer",
        "order_estimated_delivery_date": "estimated_delivery"
    })

    date_cols = ["ordered_at", "approved_at", "delivered_carrier",
                 "delivered_customer", "estimated_delivery"]
    for col in date_cols:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")

    orders = orders[["source_id", "customer_id", "status", "ordered_at",
                     "approved_at"]].dropna(subset=["customer_id"])
    orders.to_sql("orders", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(orders):,} orders")
    return orders

def generate_sessions(core_engine):
    """
    SYNTHETIC DATA: Generate funnel sessions from order data.
    For each order, create 5 session stages (visit → purchase).
    For non-converted visits, randomly drop off at earlier stages.
    This simulates a realistic purchase funnel for analysis.
    """
    orders = pd.read_sql("""
        SELECT order_id, customer_id, ordered_at
        FROM orders LIMIT 50000
    """, core_engine)

    stages = ["visit", "product_view", "add_to_cart", "checkout", "purchase"]
    sessions = []

    for _, row in orders.iterrows():
        # Completed orders get all 5 stages
        for i, stage in enumerate(stages):
            sessions.append({
                "customer_id": row["customer_id"],
                "order_id": row["order_id"] if stage == "purchase" else None,
                "channel": np.random.choice(
                    ["organic_search", "paid_search", "social", "email", "direct"],
                    p=[0.35, 0.25, 0.15, 0.15, 0.10]
                ),
                "stage": stage,
                "stage_order": i + 1,
                "session_ts": row["ordered_at"] - pd.Timedelta(minutes=30 * (5 - i))
            })

    # Add ~40% extra sessions that DROP OFF before purchase (real)
    n_abandoned = int(len(orders) * 0.4)
    for _ in range(n_abandoned):
        drop_stage = np.random.choice([1, 2, 3, 4], p=[0.15, 0.30, 0.35, 0.20])
        ref_row = orders.sample(1).iloc[0]
        for i in range(drop_stage):
            sessions.append({
                "customer_id": ref_row["customer_id"],
                "order_id": None,
                "channel": np.random.choice(
                    ["organic_search", "paid_search", "social", "email", "direct"]
                ),
                "stage": stages[i],
                "stage_order": i + 1,
                "session_ts": ref_row["ordered_at"] - pd.Timedelta(days=np.random.randint(1, 30))
            })

    df = pd.DataFrame(sessions)
    df.to_sql("sessions", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} sessions generated (with funnel drop-offs)")

def generate_campaigns(core_engine):
    """SYNTHETIC: Create marketing campaign data for ROAS analysis."""
    campaigns = pd.DataFrame([
        {"channel": "paid_search",    "name": "Google Ads Q1",     "budget": 50000, "spend": 47200, "start_dt": "2017-01-01", "end_dt": "2017-03-31"},
        {"channel": "paid_search",    "name": "Google Ads Q2",     "budget": 55000, "spend": 52800, "start_dt": "2017-04-01", "end_dt": "2017-06-30"},
        {"channel": "social",         "name": "Facebook Summer",   "budget": 30000, "spend": 28500, "start_dt": "2017-06-01", "end_dt": "2017-08-31"},
        {"channel": "social",         "name": "Instagram Fall",    "budget": 25000, "spend": 24100, "start_dt": "2017-09-01", "end_dt": "2017-11-30"},
        {"channel": "email",          "name": "Newsletter H1",     "budget": 10000, "spend": 9200,  "start_dt": "2017-01-01", "end_dt": "2017-06-30"},
        {"channel": "email",          "name": "Newsletter H2",     "budget": 12000, "spend": 11400, "start_dt": "2017-07-01", "end_dt": "2017-12-31"},
        {"channel": "organic_search", "name": "SEO Content",       "budget": 20000, "spend": 18000, "start_dt": "2017-01-01", "end_dt": "2017-12-31"},
        {"channel": "direct",         "name": "Brand Awareness",   "budget": 15000, "spend": 14200, "start_dt": "2017-01-01", "end_dt": "2017-12-31"},
    ])
    campaigns.to_sql("campaigns", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(campaigns)} campaigns")

def generate_ab_events(core_engine):
    """SYNTHETIC: Assign A/B test variants to sessions deterministically."""
    sessions = pd.read_sql("""
        SELECT session_id, stage, stage_order
        FROM sessions
        WHERE stage IN ('checkout', 'purchase')
        LIMIT 30000
    """, core_engine)

    ab_events = []
    for _, row in sessions.iterrows():
        variant = deterministic_variant(str(row["session_id"]), "homepage_v2")
        converted = 1 if row["stage"] == "purchase" else 0

        # Variant group gets a 12% lift in conversion (simulated)
        if variant == "variant" and not converted:
            converted = 1 if np.random.random() < 0.12 else 0

        ab_events.append({
            "session_id": row["session_id"],
            "experiment_id": "homepage_v2",
            "variant": variant,
            "converted": converted
        })

    df = pd.DataFrame(ab_events)
    df.to_sql("ab_events", core_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} A/B events (homepage_v2 experiment)")

def run_all():
    stg = get_engine("ecom_staging")
    core = get_engine("ecom_core")

    print("--- Categories ---")
    transform_categories(stg, core)
    print("--- Customers ---")
    transform_customers(stg, core)
    print("--- Products ---")
    transform_products(stg, core)
    print("--- Orders ---")
    transform_orders(stg, core)
    print("--- Sessions (synthetic) ---")
    generate_sessions(core)
    print("--- Campaigns (synthetic) ---")
    generate_campaigns(core)
    print("--- A/B Events (synthetic) ---")
    generate_ab_events(core)

if __name__ == "__main__":
    print("=== TRANSFORM PHASE ===")
    run_all()
    print("=== TRANSFORM COMPLETE ===")