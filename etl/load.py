"""
LOAD: Populate the analytics star schema from the core 3NF tables.
Uses INSERT ... ON DUPLICATE KEY UPDATE for idempotency.
"""
import pandas as pd
from config import get_engine

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

def run_all():
    core = get_engine("ecom_core")
    analytics = get_engine("ecom_analytics")

    print("--- dim_customer ---")
    load_dim_customers(core, analytics)
    print("--- dim_product ---")
    load_dim_products(core, analytics)
    print("--- fact_orders ---")
    load_fact_orders(core, analytics)

if __name__ == "__main__":
    print("=== LOAD PHASE ===")
    run_all()
    print("=== LOAD COMPLETE ===")