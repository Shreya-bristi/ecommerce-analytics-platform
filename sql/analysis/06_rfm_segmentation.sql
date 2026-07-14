-- ================================================
-- RFM SEGMENTATION (Recency, Frequency, Monetary)
-- Segments customers into High/Mid/Low value tiers
-- ================================================
USE ecom_core;

WITH rfm_raw AS (
    SELECT
        c.customer_id,
        c.city,
        c.state,
        DATEDIFF('2018-10-01', MAX(o.ordered_at))    AS recency_days,
        COUNT(DISTINCT o.order_id)                     AS frequency,
        ROUND(SUM(oi.unit_price), 2)                   AS monetary
    FROM customers c
    JOIN orders o USING (customer_id)
    JOIN order_items oi USING (order_id)
    GROUP BY c.customer_id, c.city, c.state
),

rfm_scored AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC)    AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)        AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)         AS m_score
    FROM rfm_raw
)

SELECT
    customer_id,
    city,
    state,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
        WHEN (r_score + f_score + m_score) >= 4  THEN 'At Risk'
        ELSE 'Hibernating'
    END AS segment
FROM rfm_scored
ORDER BY rfm_total DESC;
