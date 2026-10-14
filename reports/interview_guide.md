# Retail Intelligence: Technical & Behavioral Interview Defense Guide

This guide is designed for a Computer Science student or junior data analyst to confidently defend the architectural, analytical, and business decisions made in this project during technical and behavioral interviews.

---

## 1. Core Analytics & Metric Formulation

### Q1: Why is overall profit margin calculated as $\frac{\sum \text{Profit}}{\sum \text{Sales}}$ rather than the arithmetic average of line-item margins (`df['margin'].mean()`)?
> **Model Answer:**  
> "Taking the arithmetic mean of individual line-item margins creates a classic mathematical distortion known as **Simpson’s Paradox**. An arithmetic average treats every transaction equally regardless of size: a $10 sale with a +50% margin ($5 profit) would carry the exact same mathematical weight as a $1,000 corporate sale with a -10% margin (-$100 profit).  
> The arithmetic average of those two rows would be $+20\%$ $\left(\frac{50\% - 10\%}{2}\right)$, falsely suggesting strong profitability. In reality, the business lost -$95 on $1,010 in revenue, which is a **-9.41% aggregate margin** $\left(\frac{5 - 100}{10 + 1000}\right)$. In financial analysis, portfolio margins must always aggregate the numerator and denominator across the entire population before dividing."

---

### Q2: Why is counting distinct order IDs (`COUNT(DISTINCT order_id)`) critical in this dataset instead of counting rows?
> **Model Answer:**  
> "Superstore is a **line-item transactional dataset**, meaning every row represents a single SKU within an order. If a customer buys a desk, chair, and pen in one purchase, that single order generates 3 rows in the table.  
> If an analyst uses `COUNT(*)` to measure order volume or divides total sales by `COUNT(*)`, they are calculating **Average Line-Item Value** (~$230), not **Average Order Value (AOV)** ($458.61). Calculating order counts requires `COUNT(DISTINCT order_id)` (5,009 unique orders across 9,994 line items) to avoid double-counting order-level overhead, shipping economics, and customer baskets."

---

### Q3: What is the semantic difference between your 'Sales-Weighted Discount Proxy' (14.04%) and 'Gross List Discount Rate' (19.79%)?
> **Model Answer:**  
> "In the Superstore schema, the `Sales` column already represents **net post-discount transaction revenue** ($\text{Sales} = \text{Quantity} \times \text{List Price} \times (1 - \text{Discount})$).  
> If you compute $\frac{\sum \text{Sales} \times \text{Discount}}{\sum \text{Sales}}$, you are weighting discounts by net realized dollars. Because heavily discounted items generate lower net sales, this metric naturally under-weights deep-discount transactions, serving as a **net-revenue-weighted proxy** (14.04%).  
> If you estimate original catalogue list price $\left(\sum \frac{\text{Sales}}{1 - \text{Discount}} = \$2.86\text{M}\right)$, the total gross dollar concession is **$566,734.18**, representing a true **gross list discount rate of 19.79%**. In an interview, acknowledging this distinction demonstrates that you understand the underlying accounting semantics rather than blindly applying formulas."

---

## 2. SQL Architecture & Analytical Queries

### Q4: Walk me through the advanced SQL features you used in this project.
> **Model Answer:**  
> "I designed modular, production-grade SQL scripts in SQLite incorporating:
> 1. **Common Table Expressions (CTEs):** Used in `03_category_profitability.sql` and `06_customer_value.sql` to break multi-stage aggregations into readable, modular logical steps rather than writing fragile nested subqueries.
> 2. **Window Functions:**
>    - `RANK() OVER (PARTITION BY category ORDER BY total_profit DESC)` to evaluate subcategory performance within its parent division.
>    - `LAG(profit_margin_pct) OVER (ORDER BY min_discount ASC)` in `05_discount_impact.sql` to compute the step-change margin drop between consecutive discount tiers and detect the 20% cliff.
>    - `NTILE(10) OVER (ORDER BY lifetime_profit DESC)` in `06_customer_value.sql` to segment 793 customers into deciles and prove an 80/20 Pareto distribution.
>    - `SUM(...) OVER ()` to compute relative percentage share of total company profit without requiring a separate self-join.
> 3. **Defensive Zero Handling:** Used `NULLIF(SUM(sales), 0)` to guarantee queries never throw division-by-zero runtime exceptions."

---

### Q5: How did you optimize query execution on the SQLite analytical database?
> **Model Answer:**  
> "I added targeted B-tree indexes in `01_schema.sql` on columns frequently used in filtering, grouping, and joins:
> - `idx_orders_order_id` on `order_id` for distinct order deduplication.
> - `idx_orders_customer_id` on `customer_id` for customer lifetime aggregation.
> - `idx_orders_category_subcategory` on `(category, sub_category)` for composite group-bys.
> - `idx_orders_discount_band` and `idx_orders_profit` to accelerate partition scans."

---

## 3. Data Engineering & Defensive Validation

### Q6: How did you ensure data quality and handle real-world anomalies like missing postal codes?
> **Model Answer:**  
> "I built an automated validation suite in `src/data/validate.py` that asserts:
> - **Schema integrity:** All mandatory columns exist.
> - **Domain logic:** Sales $\ge 0$, Quantity $\ge 1$, Discount $\in [0, 1]$.
> - **Temporal integrity:** Shipping date is never earlier than order date ($\text{ship\_date} \ge \text{order\_date}$).
> - **Postal Code Anomaly:** In standard Superstore data, ZIP codes are often parsed as floats (e.g. `42420.0`), dropping leading zeros from East Coast ZIPs (e.g. `00501`), and Burlington, Vermont has missing ZIP codes. My cleaning script converts floats to strings, pads numeric codes to 5 digits using `.zfill(5)`, and cleanly preserves missing records without crashing downstream pipelines."

---

### Q7: How did you prove that your Python pipeline and SQL database match?
> **Model Answer:**  
> "I wrote an automated reconciliation test suite in `tests/test_reconciliation.py` using `pytest`. The test loads `retail_orders_clean.csv`, calculates executive KPIs via the Python engine, executes `sql/02_kpi_summary.sql` against `retail.db`, and asserts equality within floating-point tolerance ($\pm \$0.01$). This guarantees zero architectural drift between the analytics engineer's data warehouse layer and the data analyst's reporting layer."

---

## 4. Business Acumen & Discount Governance

### Q8: The data shows that transactions discounted >20% have negative margins. Does discounting cause the losses? Can we just ban discounts over 20% and save $135K?
> **Model Answer:**  
> "No, and claiming so would be an analytical mistake:
> 1. **Correlation $\neq$ Causation:** Discounting is strongly associated with losses in this dataset, but discounting may be applied to products that already suffer from high freight or uncompetitive wholesale costs (like Tables).
> 2. **Basket Halo Effects:** Banning discounts >20% might protect line-item margins, but customers buying a discounted table might also buy full-margin chairs, lighting, and accessories in the same basket. A blunt ban could cause cart abandonment.
> 3. **The Correct Recommendation:** Rather than a blunt ban, the business should implement **discount governance**: cap discretionary sales rep discounts at 20%, require VP approval for larger concessions, transition chronic loss subcategories (Tables, Bookcases) to bundle-only pricing, and enforce account-level margin floors on Decile 10 corporate clients."

---

## 5. Power BI & Dimensional Modeling

### Q9: Why did you design a Star Schema for Power BI instead of just importing the flat clean table?
> **Model Answer:**  
> "Power BI’s internal columnar engine (VertiPaq) is specifically optimized for Star Schemas. By splitting the table into `Fact_Orders` and dedicated dimensions (`Dim_Date`, `Dim_Product`, `Dim_Customer`, `Dim_Geography`):
> 1. **Dictionary Encoding:** VertiPaq compresses dimension attributes much more efficiently than repeating text strings across 10,000 fact rows.
> 2. **Standard Time Intelligence:** Having a dedicated, contiguous `Dim_Date` table marked as a Date Table is required for DAX functions like `SAMEPERIODLASTYEAR`.
> 3. **Filter Clarity:** Single-direction `1:*` relationships eliminate ambiguity and prevent circular filter dependencies."

---

## 6. Project Limitations & Future Improvements

### Q10: What are the main limitations of this project, and what would you build next?
> **Model Answer:**  
> "If given more data and time, I would address three key limitations:
> 1. **Synthetic Nature of the Dataset:** Superstore is a public educational benchmark. It lacks inventory carrying costs, return logistics data, and marketing spend.
> 2. **Customer Acquisition Cost (CAC) & LTV:** We analyzed gross customer profit, but without CAC or servicing overhead, we cannot calculate true Net Customer Lifetime Value.
> 3. **Next Steps:** I would build an **econometric price elasticity model** in Python to estimate demand curves across subcategories, allowing us to simulate the volume impact of reducing discounts from 30% to 20% before changing commercial policy."
