-- ================================================
-- CUSTOMER LIFETIME VALUE BY MONTHLY COHORT
-- Cumulative revenue per cohort over time
-- ================================================
USE ecom_core;

WITH first_purchase AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(ordered_at), '%Y-%m-01') AS cohort_month
    FROM orders
    GROUP BY customer_id
),
monthly_revenue AS (
    SELECT
        fp.cohort_month,
        TIMESTAMPDIFF(MONTH,
            fp.cohort_month,
            DATE_FORMAT(o.ordered_at, '%Y-%m-01')
        ) AS month_number,
        COUNT(DISTINCT o.customer_id)   AS active_customers,
        SUM(oi.unit_price)              AS revenue
    FROM first_purchase fp
    JOIN orders o USING (customer_id)
    JOIN order_items oi USING (order_id)
    GROUP BY fp.cohort_month, month_number
)
SELECT
    cohort_month,
    month_number,
    active_customers,
    revenue,
    SUM(revenue) OVER (
        PARTITION BY cohort_month
        ORDER BY month_number
    ) AS cumulative_ltv,
    ROUND(
        SUM(revenue) OVER (
            PARTITION BY cohort_month
            ORDER BY month_number
        ) / active_customers, 2
    ) AS ltv_per_customer
FROM monthly_revenue
ORDER BY cohort_month, month_number;