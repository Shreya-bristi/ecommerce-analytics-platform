"""
LOAD: Populate the analytics star schema from the core 3NF tables.
Uses INSERT ... ON DUPLICATE KEY UPDATE for idempotency.
"""
import pandas as pd
from config import get_engine
from sqlalchemy import text

def load_dim_customers(core_engine, analytics_engine):
    """Denormalise customer info + compute aggregates."""
    df = pd.read_sql("""
        SELECT
            c.customer_id,
            c.unique_id,
            c.city,
            c.state,
            MIN(o.ordered_at) AS first_order_dt,
            COUNT(o.order_id) AS total_orders,
            COALESCE(SUM(oi.unit_price), 0) AS total_spend
        FROM customers c
        LEFT JOIN orders o USING(customer_id)
        LEFT JOIN order_items oi USING(order_id)
        GROUP BY c.customer_id, c.unique_id, c.city, c.state
    """, core_engine)

    df["customer_tier"] = df["total_orders"].apply(
        lambda x: "vip" if x >= 3 else ("returning" if x >= 2 else "new")
    )
    df.to_sql("dim_customer", analytics_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} dim_customer rows")

def load_dim_products(core_engine, analytics_engine):
    df = pd.read_sql("""
        SELECT
            p.product_id,
            p.source_id,
            cat.name_en AS category_en,
            cat.name_pt AS category_pt,
            p.weight_g,
            ROUND(AVG(oi.unit_price), 2) AS avg_price
        FROM products p
        LEFT JOIN categories cat USING(category_id)
        LEFT JOIN order_items oi USING(product_id)
        GROUP BY p.product_id, p.source_id, cat.name_en, cat.name_pt, p.weight_g
    """, core_engine)
    df.to_sql("dim_product", analytics_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} dim_product rows")

def load_fact_orders(core_engine, analytics_engine):
    df = pd.read_sql("""
        SELECT
            o.order_id,
            CAST(DATE_FORMAT(o.ordered_at, '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            o.customer_id,
            o.status,
            COUNT(oi.item_id) AS item_count,
            SUM(oi.unit_price) AS revenue,
            SUM(oi.freight) AS freight_total
        FROM orders o
        JOIN order_items oi USING(order_id)
        GROUP BY o.order_id, o.ordered_at, o.customer_id, o.status
    """, core_engine)

    # Map customer_id to customer_key
    dim_cust = pd.read_sql(
        "SELECT customer_key, customer_id FROM dim_customer", analytics_engine
    )
    df = df.merge(dim_cust, on="customer_id", how="left")
    df = df.drop(columns=["customer_id"])

    df.to_sql("fact_orders", analytics_engine, if_exists="append", index=False)
    print(f"  ✓ {len(df):,} fact_orders rows")


def load_dim_channels(analytics_engine):
    """Populate dim_channel with distinct channel names."""
    df = pd.DataFrame([
        {"channel_name": "organic_search"},
        {"channel_name": "paid_search"},
        {"channel_name": "social"},
        {"channel_name": "email"},
        {"channel_name": "direct"},
    ])
    df.to_sql("dim_channel", analytics_engine, if_exists="append", index=False)
    print(f"  \u2713 {len(df)} dim_channel rows")


def load_fact_sessions(core_engine, analytics_engine):
    """Load sessions into fact_sessions with surrogate key lookups."""
    df = pd.read_sql("""
        SELECT
            s.session_id,
            CAST(DATE_FORMAT(s.session_ts, '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            s.customer_id,
            s.channel,
            s.stage,
            s.stage_order
        FROM sessions s
    """, core_engine)

    # Map customer_id to customer_key
    dim_cust = pd.read_sql(
        "SELECT customer_key, customer_id FROM dim_customer", analytics_engine
    )
    df = df.merge(dim_cust, on="customer_id", how="left")

    # Map channel to channel_key
    dim_ch = pd.read_sql(
        "SELECT channel_key, channel_name FROM dim_channel", analytics_engine
    )
    df = df.merge(dim_ch, left_on="channel", right_on="channel_name", how="left")

    # Add converted flag
    df["converted"] = (df["stage"] == "purchase").astype(int)

    # Keep only the columns that match fact_sessions
    df = df[["session_id", "date_key", "customer_key", "channel_key",
             "stage", "stage_order", "converted"]]
    df = df.dropna(subset=["customer_key", "date_key"])
    df["customer_key"] = df["customer_key"].astype(int)
    df["date_key"] = df["date_key"].astype(int)

    df.to_sql("fact_sessions", analytics_engine, if_exists="append", index=False)
    print(f"  \u2713 {len(df):,} fact_sessions rows")

def run_all():
    core = get_engine("ecom_core")
    analytics = get_engine("ecom_analytics")

    # Clearing analytics tables for idempotent re-runs
    with analytics.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for t in ["fact_ab_events", "fact_sessions", "fact_orders",
                  "dim_customer", "dim_product", "dim_channel", "dim_campaign"]:
            conn.execute(text(f"TRUNCATE TABLE {t}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    print("--- dim_customer ---")
    load_dim_customers(core, analytics)
    print("--- dim_product ---")
    load_dim_products(core, analytics)
    print("--- dim_channel ---")
    load_dim_channels(analytics)
    print("--- fact_orders ---")
    load_fact_orders(core, analytics)
    print("--- fact_sessions ---")
    load_fact_sessions(core, analytics)
    

if __name__ == "__main__":
    print("=== LOAD PHASE ===")
    run_all()
    print("=== LOAD COMPLETE ===")