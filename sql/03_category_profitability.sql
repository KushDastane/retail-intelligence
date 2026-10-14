-- ============================================================================
-- Query 03: Category & Sub-Category Profitability Rankings
-- Business Question: Which categories and subcategories drive profitability,
-- and which are persistent loss leaders that destroy value?
--
-- Features Used:
-- 1. CTE (Common Table Expression) for structured aggregation.
-- 2. Window Functions:
--    - RANK() OVER (...) for overall profit rank.
--    - RANK() OVER (PARTITION BY category ...) for rank within parent category.
--    - SUM(...) OVER () to calculate contribution share of total company profit.
-- ============================================================================

WITH subcategory_metrics AS (
    SELECT
        category,
        sub_category,
        COUNT(DISTINCT order_id) AS orders_count,
        COUNT(*) AS line_items_count,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS profit_margin_pct,
        ROUND(SUM(sales * discount) * 100.0 / NULLIF(SUM(sales), 0), 2) AS weighted_discount_pct,
        -- Loss Metrics
        ROUND(SUM(CASE WHEN profit < 0 THEN profit ELSE 0.0 END), 2) AS loss_dollars,
        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS loss_items_count,
        ROUND(
            SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS loss_item_share_pct
    FROM retail_orders
    GROUP BY category, sub_category
)
SELECT
    category,
    sub_category,
    orders_count,
    line_items_count,
    total_sales,
    total_profit,
    profit_margin_pct,
    weighted_discount_pct,
    loss_dollars,
    loss_items_count,
    loss_item_share_pct,
    -- Analytical Window Rankings
    RANK() OVER (ORDER BY total_profit DESC) AS company_profit_rank,
    RANK() OVER (PARTITION BY category ORDER BY total_profit DESC) AS category_profit_rank,
    ROUND(total_profit * 100.0 / SUM(total_profit) OVER (), 2) AS pct_share_of_total_profit
FROM subcategory_metrics
ORDER BY company_profit_rank ASC;
