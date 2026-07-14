USE ecom_analytics;
SET cte_max_recursion_depth = 2000;

-- Generate dates from 2016-01-01 to 2019-12-31
INSERT INTO dim_date (
    date_key, full_date, day_of_week, day_name,
    month_num, month_name, quarter, year, is_weekend
)
WITH RECURSIVE dates AS (
    SELECT DATE('2016-01-01') AS d
    UNION ALL
    SELECT d + INTERVAL 1 DAY FROM dates
    WHERE d < '2019-12-31'
)

SELECT
    CAST(DATE_FORMAT(d, '%Y%m%d') AS UNSIGNED)  AS date_key,
    d                                            AS full_date,
    DAYOFWEEK(d)                                 AS day_of_week,
    DAYNAME(d)                                   AS day_name,
    MONTH(d)                                     AS month_num,
    MONTHNAME(d)                                 AS month_name,
    QUARTER(d)                                   AS quarter,
    YEAR(d)                                      AS year,
    IF(DAYOFWEEK(d) IN (1,7), 1, 0)             AS is_weekend
FROM dates;
