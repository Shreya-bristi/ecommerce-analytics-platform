-- ================================================
-- CATEGORY HIERARCHY WITH REVENUE ROLL-UP
-- Recursive CTE traverses the category tree
-- ================================================
USE ecom_core;

WITH RECURSIVE cat_tree AS (
    -- Anchor: top-level categories (no parent)
    SELECT
        category_id,
        name_en,
        parent_id,
        CAST(name_en AS CHAR(500)) AS full_path,
        0 AS depth
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive: child categories
    SELECT
        c.category_id,
        c.name_en,
        c.parent_id,
        CONCAT(ct.full_path, ' > ', c.name_en),
        ct.depth + 1
    FROM categories c
    JOIN cat_tree ct ON c.parent_id = ct.category_id
)
SELECT
    ct.full_path       AS category_path,
    ct.depth,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.unit_price) AS revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_item_price,
    RANK() OVER (ORDER BY SUM(oi.unit_price) DESC) AS revenue_rank
FROM cat_tree ct
JOIN products p USING (category_id)
JOIN order_items oi USING (product_id)
JOIN orders o USING (order_id)
GROUP BY ct.full_path, ct.depth
ORDER BY revenue DESC
LIMIT 20;