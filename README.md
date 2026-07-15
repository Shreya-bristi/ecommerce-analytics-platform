# E-Commerce Analytics Platform

*Production-grade analytics pipeline — from raw transactional data to executive dashboards, with automated testing and CI/CD.*

---

## Problem Statement

> The Olist Brazilian E-Commerce dataset contains 100K+ real orders, 96K customers, and 33K products across 9 raw CSV files — but no marketing attribution, no funnel data, and no experiment tracking. Using Python (pandas, SQLAlchemy), MySQL, and Power BI, I engineered a full medallion-architecture pipeline: normalised raw data into a 3NF operational schema, generated synthetic sessions and A/B test events to simulate real business telemetry, and built a star schema consumed by a five-page Power BI dashboard — surfacing $13.17M in revenue insights, a 31% funnel drop-off at checkout, a 61.81x ROAS for organic search, and a statistically significant homepage A/B test result (z = 9.24, p < 0.05).

---

## Key Results

| Metric                         | Value                          |
|--------------------------------|--------------------------------|
| Total Revenue                  | $13.17M                        |
| Total Orders                   | 95K                            |
| Average Order Value            | $138.13                        |
| Funnel Conversion (end-to-end) | 71.4% (synthetic)              |
| Biggest Drop-off Stage         | Checkout — 11.56%              |
| Best ROAS Channel              | Organic Search — 61.81x        |
| Worst ROAS Channel             | Paid Search — 1.97–2.85x       |
| VIP Customer LTV               | $304.37 vs $129.81 (new)       |
| A/B Test Lift                  | +31% CVR (11.71% → 15.36%)    |
| A/B Statistical Significance   | Z = 9.24 > 1.96 threshold     |

---

## What I Built

✦ **ETL Pipeline** — Python scripts ingesting 9 CSVs into a 3-layer MySQL architecture (staging → 3NF core → star schema), with idempotent UPSERT logic and FK-safe re-runs

✦ **Data Modelling** — 8-table 3NF operational schema (ecom_core) + 8-table star schema (3 facts, 5 dims) optimised for Power BI DirectQuery

✦ **Normalisation** — Eliminated transitive dependencies across customers, campaigns, categories, and order_items; FK constraints enforced at the DB level

✦ **Complex SQL** — 6 production-grade queries: funnel drop-off (LAG window), marketing ROAS (4-table JOIN), LTV cohorts (running SUM OVER PARTITION), A/B z-test (pure SQL statistics), category hierarchy (recursive CTE), RFM segmentation (NTILE quartiles)

✦ **A/B Testing** — Deterministic variant assignment via MD5 hash; SQL z-test measuring 3% CVR lift at 95% confidence; visualised in Power BI with gauge + significance badge

✦ **CI/CD Pipeline** — GitHub Actions: SQL linting (sqlfluff) + pytest on every push; Flyway schema migrations for versioned schema deployment

---

## Tech Stack

`MySQL 8.0` · `Python (pandas, SQLAlchemy, pymysql)` · `Power BI Desktop` · `GitHub Actions` · `Flyway` · `sqlfluff`
