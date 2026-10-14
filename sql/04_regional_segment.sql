-- ============================================================================
-- Query 04: Regional & Customer Segment Profitability Matrix
-- Business Question: How does profitability vary across geographic regions
-- and customer segments, and where are margins being drained?
--
-- Features Used:
-- 1. CTE for Region x Segment aggregation.
-- 2. Window Functions:
--    - SUM(...) OVER (PARTITION BY region) to calculate segment profit share
--      within each geographic territory.
--    - RANK() OVER (ORDER BY total_profit DESC) for global territory ranking.
-- ============================================================================

WITH region_segment_summary AS (
    SELECT
        region,
        segment,
        COUNT(DISTINCT customer_id) AS customer_count,
        COUNT(DISTINCT order_id) AS orders_count,
        COUNT(*) AS total_line_items,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS profit_margin_pct,
        ROUND(SUM(sales * discount) * 100.0 / NULLIF(SUM(sales), 0), 2) AS weighted_discount_pct,
        -- Loss Metrics
        ROUND(SUM(CASE WHEN profit < 0 THEN profit ELSE 0.0 END), 2) AS total_loss_dollars,
        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS loss_line_items,
        ROUND(
            SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS loss_item_share_pct
    FROM retail_orders
    GROUP BY region, segment
)
SELECT
    region,
    segment,
    customer_count,
    orders_count,
    total_sales,
    total_profit,
    profit_margin_pct,
    weighted_discount_pct,
    total_loss_dollars,
    loss_item_share_pct,
    -- Window calculations
    ROUND(
        total_profit * 100.0 / NULLIF(SUM(total_profit) OVER (PARTITION BY region), 0),
        2
    ) AS segment_share_of_region_profit,
    RANK() OVER (ORDER BY total_profit DESC) AS rank_across_segments
FROM region_segment_summary
ORDER BY region, total_profit DESC;
