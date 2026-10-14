-- ============================================================================
-- Query 02: Executive KPI Summary Scorecard
-- Business Question: What are the executive topline metrics, transaction
-- volumes, and overall loss footprint of the business?
--
-- Analytical Rules:
-- 1. Distinct orders counted via COUNT(DISTINCT order_id) (never line items).
-- 2. Overall margin calculated as SUM(profit) / SUM(sales) (never row mean).
-- 3. Division by zero prevented with NULLIF().
-- ============================================================================

SELECT
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
    -- Loss Footprint
    ROUND(SUM(CASE WHEN profit < 0 THEN profit ELSE 0.0 END), 2) AS total_loss_dollars,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS loss_line_items,
    ROUND(SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS loss_item_share_pct,
    COUNT(DISTINCT CASE WHEN profit < 0 THEN order_id END) AS loss_orders_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN profit < 0 THEN order_id END) * 100.0
        / NULLIF(COUNT(DISTINCT order_id), 0),
        2
    ) AS loss_order_share_pct,
    -- Discount Measures
    ROUND(SUM(sales * discount) * 100.0 / NULLIF(SUM(sales), 0), 2) AS net_sales_weighted_discount_pct,
    ROUND(AVG(discount) * 100.0, 2) AS simple_avg_discount_pct
FROM retail_orders;
