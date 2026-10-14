-- ============================================================================
-- Query 06: Customer Profitability Concentration & Decile Pareto Analysis
-- Business Question: How concentrated is profit across the customer base,
-- and which customer deciles generate value versus destroy capital?
--
-- Features Used:
-- 1. First CTE: Aggregates total lifetime sales, profit, orders per customer.
-- 2. Second CTE: Employs NTILE(10) window function to split customers into deciles.
-- 3. Third Level: Computes cumulative profit share and decile margin decay.
-- ============================================================================

WITH customer_totals AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(*) AS total_items,
        ROUND(SUM(sales), 2) AS lifetime_sales,
        ROUND(SUM(profit), 2) AS lifetime_profit,
        ROUND(SUM(sales * discount) * 100.0 / NULLIF(SUM(sales), 0), 2) AS weighted_discount_pct
    FROM retail_orders
    GROUP BY customer_id, customer_name, segment
),
customer_deciles AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        total_orders,
        lifetime_sales,
        lifetime_profit,
        weighted_discount_pct,
        NTILE(10) OVER (ORDER BY lifetime_profit DESC) AS profit_decile
    FROM customer_totals
)
SELECT
    profit_decile,
    COUNT(*) AS customer_count,
    ROUND(SUM(lifetime_sales), 2) AS decile_sales,
    ROUND(SUM(lifetime_profit), 2) AS decile_profit,
    ROUND(SUM(lifetime_profit) * 100.0 / NULLIF(SUM(lifetime_sales), 0), 2) AS decile_profit_margin_pct,
    ROUND(AVG(total_orders), 1) AS avg_orders_per_customer,
    ROUND(
        SUM(lifetime_sales * weighted_discount_pct) / NULLIF(SUM(lifetime_sales), 0),
        2
    ) AS avg_discount_pct,
    -- Cumulative profit curve across deciles
    ROUND(SUM(SUM(lifetime_profit)) OVER (ORDER BY profit_decile ASC), 2) AS cumulative_profit,
    ROUND(
        SUM(lifetime_profit) * 100.0 / SUM(SUM(lifetime_profit)) OVER (),
        2
    ) AS decile_share_of_total_profit_pct
FROM customer_deciles
GROUP BY profit_decile
ORDER BY profit_decile ASC;
