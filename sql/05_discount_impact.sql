-- ============================================================================
-- Query 05: Discount Band Profitability & Margin Decay Analysis
-- Business Question: At what discount threshold does transaction profitability
-- collapse, and how severe is the margin erosion across discount tiers?
--
-- Features Used:
-- 1. CTE aggregating metrics across retail discount bands.
-- 2. Window Functions:
--    - LAG(profit_margin_pct) OVER (ORDER BY min_discount ASC) to calculate
--      the step-change margin drop from the previous discount tier.
--    - SUM(total_profit) OVER (ORDER BY min_discount ASC) to track
--      cumulative company profit as discounting intensifies.
-- ============================================================================

WITH discount_tier_metrics AS (
    SELECT
        discount_band,
        MIN(discount) AS min_discount,
        MAX(discount) AS max_discount,
        COUNT(*) AS total_line_items,
        COUNT(DISTINCT order_id) AS total_orders_affected,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS profit_margin_pct,
        ROUND(AVG(discount) * 100.0, 2) AS avg_band_discount_pct,
        -- Loss Metrics
        ROUND(SUM(CASE WHEN profit < 0 THEN profit ELSE 0.0 END), 2) AS total_loss_dollars,
        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS unprofitable_items_count,
        ROUND(
            SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS unprofitable_item_pct
    FROM retail_orders
    GROUP BY discount_band
)
SELECT
    discount_band,
    total_line_items,
    total_orders_affected,
    total_sales,
    total_profit,
    profit_margin_pct,
    -- Margin drop relative to preceding tier (cliff analysis)
    ROUND(
        profit_margin_pct - LAG(profit_margin_pct) OVER (ORDER BY min_discount ASC),
        2
    ) AS margin_change_vs_prior_tier_pct,
    -- Cumulative profit accumulation
    ROUND(SUM(total_profit) OVER (ORDER BY min_discount ASC), 2) AS cumulative_profit,
    unprofitable_items_count,
    unprofitable_item_pct,
    total_loss_dollars
FROM discount_tier_metrics
ORDER BY min_discount ASC;
