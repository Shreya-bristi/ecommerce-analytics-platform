-- ================================================
-- MARKETING CHANNEL ROAS (Return on Ad Spend)
-- Revenue and margin per dollar of ad spend
-- ================================================
USE ecom_core;

SELECT
    c.channel,
    c.name                                          AS campaign_name,
    c.spend                                         AS total_spend,
    COUNT(DISTINCT o.order_id)                      AS orders_driven,
    SUM(oi.unit_price)                              AS total_revenue,
    ROUND(SUM(oi.unit_price) / NULLIF(c.spend, 0), 2) AS roas,
    ROUND(SUM(oi.unit_price) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_value,
    ROUND(c.spend / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS cost_per_acquisition
FROM campaigns c
LEFT JOIN sessions s
    ON
        c.channel = s.channel
        AND s.session_ts BETWEEN c.start_dt AND c.end_dt
        AND s.stage = 'purchase'
LEFT JOIN orders o ON s.order_id = o.order_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.campaign_id, c.channel, c.name, c.spend
ORDER BY roas DESC;
