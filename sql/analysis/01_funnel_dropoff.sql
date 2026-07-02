-- ================================================
-- FUNNEL DROP-OFF ANALYSIS
-- Shows conversion rate and drop-off at each stage
-- ================================================
USE ecom_core;

WITH funnel AS (
    SELECT
        stage,
        stage_order,
        COUNT(DISTINCT session_id) AS sessions
    FROM sessions
    GROUP BY stage, stage_order
),
with_prev AS (
    SELECT
        stage,
        stage_order,
        sessions,
        LAG(sessions) OVER (ORDER BY stage_order) AS prev_sessions
    FROM funnel
)
SELECT
    stage,
    sessions,
    prev_sessions,
    ROUND((sessions / prev_sessions) * 100.0, 2) AS retention_pct,
    ROUND(100 - (sessions / prev_sessions) * 100.0, 2) AS drop_off_pct
FROM with_prev
ORDER BY stage_order;