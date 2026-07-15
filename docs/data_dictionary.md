# Data Dictionary

## Overview

This project uses a **medallion lite architecture** with three MySQL schemas:

| Layer | Schema | Purpose | Design |
|-------|--------|---------|--------|
| Bronze | `ecom_staging` | Raw data landing zone | Raw CSV data loaded as-is, no transformations applied |
| Silver | `ecom_core` | Clean, normalized business data | 3NF relational model |
| Gold | `ecom_analytics` | Reporting-ready star schema | Dim/fact tables for Power BI |

Data flows: **Kaggle CSVs → ecom_staging → ecom_core → ecom_analytics → Power BI**

---

## 1. ecom_staging (Bronze Layer)

Raw data ingested from the Olist Brazilian E-Commerce Kaggle dataset. No transformations applied.
| Table | Row Count | Source File |
|-------|-----------|-------------|
| stg_customers | ~99K | olist_customers_dataset.csv |
| stg_orders | ~99K | olist_orders_dataset.csv |
| stg_order_items | ~113K | olist_order_items_dataset.csv |
| stg_payments | ~104K | olist_order_payments_dataset.csv |
| stg_products | ~33K | olist_products_dataset.csv |
| stg_category_translation | ~71 | product_category_name_translation.csv |

---

## 2. ecom_core (Silver Layer — 3NF)

Cleaned, deduplicated, and normalized. Business logic applied. Synthetic tables generated to support analytics use cases not covered by the original dataset.

### customers

| Column | Type | Description |
|--------|------|-------------|
| customer_id | INT (PK) | Surrogate key, auto-increment |
| source_id | VARCHAR(50) | Original Kaggle customer_id |
| unique_id | VARCHAR(50) | Deduplicated customer identifier |
| city | VARCHAR(100) | Customer city |
| state | VARCHAR(5) | Brazilian state code |

### orders

| Column | Type | Description |
|--------|------|-------------|
| order_id | INT (PK) | Surrogate key, auto-increment |
| source_id | VARCHAR(50) | Original Kaggle `order_id` |
| customer_id | INT (FK → customers) | Purchasing customer |
| campaign_id | INT (FK → campaigns, nullable) | Attributed campaign |
| status | ENUM | Order status (`delivered`, `shipped`, `canceled`, etc.) |
| ordered_at | DATETIME | Order placed timestamp |
| approved_at | DATETIME | Payment approved timestamp |
| delivered_carrier | DATETIME | Handed to carrier timestamp |
| delivered_customer | DATETIME | Delivered to customer timestamp |
| estimated_delivery | DATETIME | Estimated delivery date |
### order_items

| Column | Type | Description |
|--------|------|-------------|
| item_id | INT (PK) | Surrogate key, auto-increment |
| order_id | INT (FK → orders) | Parent order |
| product_id | INT (FK → products) | Product purchased |
| item_seq | INT | Item sequence within order |
| unit_price | DECIMAL(10,2) | Item price in BRL |
| freight | DECIMAL(10,2) | Shipping cost for this item |
### categories

| Column | Type | Description |
|--------|------|-------------|
| category_id | INT (PK) | Surrogate key |
| name_pt | VARCHAR(100) | Category name in Portuguese |
| name_en | VARCHAR(100) | Category name in English |
| parent_id | INT (FK → categories, nullable) | Parent category for hierarchy |

### products

| Column | Type | Description |
|--------|------|-------------|
| product_id | INT (PK) | Surrogate key |
| source_id | VARCHAR(50) | Original Kaggle product_id |
| category_id | INT (FK → categories) | Product category |
| weight_g | INT | Product weight in grams |
| length_cm | INT | Package length |
| width_cm | INT | Package width |
| height_cm | INT | Package height |

### sessions *(SYNTHETIC)*

| Column | Type | Description |
|--------|------|-------------|
| session_id | INT (PK) | Surrogate key |
| customer_id | INT (FK → customers) | Session customer |
| session_ts | DATETIME | Session timestamp |
| channel | VARCHAR(20) | Acquisition channel (paid_search, organic_search, social, email, direct) |
| stage | VARCHAR(20) | Funnel stage (visit, product_view, add_to_cart, checkout, purchase) |
| stage_order | INT | Stage sequence number (1–5) |
| order_id | INT (FK → orders, nullable) | Linked order for purchase-stage sessions |

### campaigns *(SYNTHETIC)*

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | INT (PK) | Surrogate key |
| channel | VARCHAR(20) | Marketing channel |
| name | VARCHAR(100) | Campaign name (e.g., "Google Ads Q1") |
| spend | DECIMAL(10,2) | Total campaign spend in BRL |
| budget | DECIMAL(10,2) | Allocated budget in BRL |
| start_dt | DATE | Campaign start date |
| end_dt | DATE | Campaign end date |

### ab_events *(SYNTHETIC)*

| Column | Type | Description |
|--------|------|-------------|
| event_id | INT (PK) | Surrogate key, auto-increment |
| session_id | INT (FK → sessions) | Test session |
| experiment_id | VARCHAR(50) | Experiment identifier (e.g., "homepage_v2") |
| variant | VARCHAR(10) | Assignment: "control" or "variant" |
| converted | TINYINT | 1 = converted, 0 = did not convert |
| created_at | DATETIME | Record creation timestamp |

---

## 3. ecom_analytics (Gold Layer — Star Schema)

Optimized for Power BI with surrogate keys, pre-joined dimensions, and pre-computed metrics.

### dim_customer

| Column | Type | Description |
|--------|------|-------------|
| customer_key | INT (PK) | Surrogate key |
| customer_id | INT | Business key from ecom_core |
| unique_id | VARCHAR(50) | Deduplicated identifier |
| city | VARCHAR(100) | Customer city |
| state | VARCHAR(5) | Brazilian state code |
| first_order_dt | DATE | Date of customer's first purchase |
| total_orders | INT | Lifetime order count |
| total_spend | DECIMAL(10,2) | Lifetime revenue |
| customer_tier | VARCHAR(20) | Segment: "new", "returning", or "vip" |

### dim_date

| Column | Type | Description |
|--------|------|-------------|
| date_key | INT (PK) | Integer key in YYYYMMDD format |
| full_date | DATE | Calendar date |
| day_name | VARCHAR(10) | Day of week name |
| day_of_week | INT | Day of week number (1=Sun, 7=Sat) |
| month_num | INT | Month number (1–12) |
| month_name | VARCHAR(10) | Month name |
| quarter | INT | Quarter number (1–4) |
| year | INT | Calendar year |
| is_weekend | BOOLEAN | TRUE if Saturday or Sunday |

### dim_channel

| Column | Type | Description |
|--------|------|-------------|
| channel_key | INT (PK) | Surrogate key |
| channel_name | VARCHAR(20) | Channel: organic_search, paid_search, social, email, direct |

### dim_campaign

| Column | Type | Description |
|--------|------|-------------|
| campaign_key | INT (PK) | Surrogate key |
| campaign_id | INT | Business key from ecom_core |
| channel | VARCHAR(20) | Marketing channel |
| name | VARCHAR(100) | Campaign name |
| budget | DECIMAL(10,2) | Allocated budget |
| spend | DECIMAL(10,2) | Actual spend |

### dim_product

| Column | Type | Description |
|--------|------|-------------|
| product_key | INT (PK) | Surrogate key |
| product_id | INT | Business key from ecom_core |
| source_id | VARCHAR(50) | Original Kaggle product_id |
| category_en | VARCHAR(100) | English category name |
| category_pt | VARCHAR(100) | Portuguese category name |
| avg_price | DECIMAL(10,2) | Average selling price |
| weight_g | INT | Product weight in grams |

### fact_orders

| Column | Type | Description |
|--------|------|-------------|
| order_key | INT (PK) | Surrogate key |
| order_id | INT | Business key from ecom_core |
| customer_key | INT (FK → dim_customer) | Customer dimension |
| date_key | INT (FK → dim_date) | Order date dimension |
| campaign_key | INT (FK → dim_campaign) | Attributed campaign |
| revenue | DECIMAL(10,2) | Order revenue (sum of item prices) |
| payment_value | DECIMAL(10,2) | Total payment amount |
| freight_total | DECIMAL(10,2) | Total shipping cost |
| item_count | INT | Number of items in order |
| delivery_days | INT | Days from order to delivery |
| status | VARCHAR(20) | Order status |

Grain: one row per order

### fact_sessions

| Column | Type | Description |
|--------|------|-------------|
| session_key | INT (PK) | Surrogate key |
| session_id | INT | Business key from ecom_core |
| customer_key | INT (FK → dim_customer) | Session customer |
| date_key | INT (FK → dim_date) | Session date |
| channel_key | INT (FK → dim_channel) | Acquisition channel |
| stage | VARCHAR(20) | Funnel stage |
| stage_order | INT | Stage sequence (1–5) |
| converted | BOOLEAN | TRUE if session led to purchase |

Grain: one row per session-stage combination

### fact_ab_events

| Column | Type | Description |
|--------|------|-------------|
| ab_key | INT (PK) | Surrogate key |
| session_key | INT (FK → fact_sessions) | Test session |
| event_date_key | INT (FK → dim_date) | Event date |
| experiment_id | VARCHAR(50) | Experiment name |
| variant | VARCHAR(10) | "control" or "variant" |
| converted | BOOLEAN | TRUE if converted |

one row per A/B test exposure

---

## 4. Analytics Views

Pre-computed views in `ecom_analytics` for complex analytics that require cross-table logic beyond Power BI's DAX capabilities.

### marketing_roas_summary

Campaign-level ROAS with proper attribution via session date-range matching.

| Column | Type | Description |
|--------|------|-------------|
| channel | VARCHAR(20) | Marketing channel |
| campaign_name | VARCHAR(100) | Campaign name |
| total_spend | DECIMAL(10,2) | Campaign spend |
| orders_driven | INT | Orders attributed to campaign |
| total_revenue | DECIMAL(10,2) | Revenue attributed to campaign |
| roas | DECIMAL(10,2) | Return on ad spend (revenue ÷ spend) |
| cost_per_acquisition | DECIMAL(10,2) | Spend per order (spend ÷ orders) |

**Why a view?** Campaign attribution requires date-range joins (`session_ts BETWEEN start_dt AND end_dt`) which Power BI relationships cannot express — they only support exact key matching.

### ltv_cohort_summary

Customer lifetime value by first-purchase cohort month.

| Column | Type | Description |
|--------|------|-------------|
| cohort_month | DATE | Month of customer's first purchase |
| month_number | INT | Months since first purchase (0 = first month) |
| active_customers | INT | Customers with orders in this period |
| revenue | DECIMAL(10,2) | Revenue in this period |
| cumulative_ltv | DECIMAL(10,2) | Cumulative revenue for cohort |
| ltv_per_customer | DECIMAL(10,2) | Cumulative LTV per customer |

**Why a view?** Cohort month calculation requires `TIMESTAMPDIFF` between each order date and the customer's first order date — a complex per-row computation not practical in DAX.

**Note:** Olist customers are predominantly one-time buyers, so `month_number` is almost entirely 0. The view is architecturally correct for datasets with repeat purchases.

---

## 5. Synthetic Data Notes

Three tables contain **generated data** to support analytics use cases not covered by the original Olist Kaggle dataset:

| Table | Why Synthetic | Generation Method |
|-------|--------------|-------------------|
| `sessions` | Olist has no session/clickstream data | Generated from orders with realistic funnel stages and channel distribution |
| `campaigns` | Olist has no marketing spend data | 8 campaigns across 5 channels with budget and spend figures |
| `ab_events` | Olist has no A/B test data | Deterministic variant assignment via hash; control ~12% CVR, variant ~15% CVR |

**Analytical Note:** All synthetic data is clearly labeled. The Power BI dashboard includes notes where synthetic data impacts interpretation (e.g., funnel conversion rates, campaign ROAS). SQL showcase queries use the same synthetic tables but demonstrate real analytical techniques (window functions, CTEs, statistical testing).

### Generation details

- **sessions**: `deterministic_variant()` in `transform.py` uses MD5 hashing for reproducible assignment. Funnel stages distributed across visit → product_view → add_to_cart → checkout → purchase with realistic drop-off rates.
- **campaigns**: 8 static campaigns (2 per paid_search, 2 social, 2 email, 1 organic_search, 1 direct) with spend ranging from $9,200 to $52,800.
- **ab_events**: 30,000 events from `generate_ab_events()` in `transform.py`. Uses `RandomState(session_id)` for deterministic, reproducible conversion assignment. 3% lift designed to be statistically significant at 95% confidence.
