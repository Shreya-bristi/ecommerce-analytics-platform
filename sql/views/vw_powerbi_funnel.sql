-- Views that Power BI connects to directly
USE ecom_analytics;

CREATE OR REPLACE VIEW vw_funnel AS
SELECT
    dd.full_date,
    dd.month_name,
    dd.year,
    fs.stage,
    fs.stage_order,
    dc.customer_tier,
    ch.channel_name,
    COUNT(*) AS session_count
FROM fact_sessions fs
JOIN dim_date dd ON fs.date_key = dd.date_key
JOIN dim_customer dc ON fs.customer_key = dc.customer_key
LEFT JOIN dim_channel ch ON fs.channel_key = ch.channel_key
GROUP BY
    dd.full_date, dd.month_name, dd.year,
    fs.stage, fs.stage_order, dc.customer_tier, ch.channel_name;
