-- ================================================
-- A/B TEST: Homepage V2 Conversion Significance
-- Computes z-score to determine statistical significance
-- z > 1.96 = significant at 95% confidence
-- ================================================
USE ecom_core;

WITH summary AS (
    SELECT
        variant,
        COUNT(*)           AS n,
        SUM(converted)     AS conversions,
        AVG(converted)     AS conversion_rate
    FROM ab_events
    WHERE experiment_id = 'homepage_v2'
    GROUP BY variant
),

pooled AS (
    SELECT SUM(conversions) / SUM(n) AS p_pool FROM summary
),

ztest AS (
    SELECT
        ctrl.n          AS n_control,
        ctrl.conversions AS conv_control,
        ctrl.conversion_rate AS cvr_control,
        var.n           AS n_variant,
        var.conversions  AS conv_variant,
        var.conversion_rate AS cvr_variant,
        p.p_pool,
        (var.conversion_rate - ctrl.conversion_rate)
        / SQRT(p.p_pool * (1 - p.p_pool) * (1/var.n + 1/ctrl.n))
            AS z_score
    FROM summary ctrl, summary var, pooled p
    WHERE
        ctrl.variant = 'control'
        AND var.variant  = 'variant'
)

SELECT
    n_control,
    n_variant,
    ROUND(cvr_control * 100, 2)  AS control_cvr_pct,
    ROUND(cvr_variant * 100, 2)  AS variant_cvr_pct,
    ROUND((cvr_variant - cvr_control) / cvr_control * 100, 2) AS lift_pct,
    ROUND(z_score, 4)            AS z_score,
    CASE
        WHEN ABS(z_score) > 2.576 THEN 'Significant at 99%'
        WHEN ABS(z_score) > 1.960 THEN 'Significant at 95%'
        WHEN ABS(z_score) > 1.645 THEN 'Significant at 90%'
        ELSE 'Not significant'
    END AS significance
FROM ztest;
