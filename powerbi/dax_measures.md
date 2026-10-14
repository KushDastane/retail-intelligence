# Power BI DAX Measures Reference Library

All business measures should be organized inside a dedicated, disconnected measure table named `_Measures` in Power BI.

---

## 1. Core Financial & Volume Measures

### `[Total Sales]`
```dax
Total Sales = 
SUM ( Fact_Orders[sales] )
```
- **Format:** Currency (`$#,##0.00`)
- **Definition:** Total recorded post-discount net revenue.
- **Reconciled Value:** `$2,297,200.86`

---

### `[Total Profit]`
```dax
Total Profit = 
SUM ( Fact_Orders[profit] )
```
- **Format:** Currency (`$#,##0.00`)
- **Definition:** Total net financial profit after product costs and discounting.
- **Reconciled Value:** `$286,397.02`

---

### `[Profit Margin %]`
```dax
Profit Margin % = 
DIVIDE ( [Total Profit], [Total Sales], 0 )
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Overall portfolio profit margin. Uses safe division via `DIVIDE` to avoid divide-by-zero errors.
- **Reconciled Value:** `12.47%`
- **Important Note:** Never compute overall margin as `AVERAGE(Fact_Orders[line_profit_margin])`. Always divide aggregated profit by aggregated sales.

---

### `[Distinct Orders]`
```dax
Distinct Orders = 
DISTINCTCOUNT ( Fact_Orders[order_id] )
```
- **Format:** Whole Number (`#,##0`)
- **Definition:** Total number of unique orders placed by customers.
- **Reconciled Value:** `5,009` (avoids double-counting multi-item baskets).

---

### `[Distinct Customers]`
```dax
Distinct Customers = 
DISTINCTCOUNT ( Fact_Orders[customer_id] )
```
- **Format:** Whole Number (`#,##0`)
- **Definition:** Total number of unique customer accounts.
- **Reconciled Value:** `793`

---

### `[Units Sold]`
```dax
Units Sold = 
SUM ( Fact_Orders[quantity] )
```
- **Format:** Whole Number (`#,##0`)
- **Definition:** Total physical item units sold across all transactions.
- **Reconciled Value:** `37,873`

---

### `[Average Order Value]`
```dax
Average Order Value = 
DIVIDE ( [Total Sales], [Distinct Orders], 0 )
```
- **Format:** Currency (`$#,##0.00`)
- **Definition:** Average revenue generated per distinct customer order basket.
- **Reconciled Value:** `$458.61`

---

## 2. Loss Footprint & Value Leakage Measures

### `[Total Loss Dollars]`
```dax
Total Loss Dollars = 
CALCULATE (
    [Total Profit],
    Fact_Orders[profit] < 0
)
```
- **Format:** Currency (`$#,##0.00`)
- **Definition:** Cumulative dollar amount of losses on unprofitable transactions.
- **Reconciled Value:** `-$156,131.29`

---

### `[Loss Line Items]`
```dax
Loss Line Items = 
CALCULATE (
    COUNTROWS ( Fact_Orders ),
    Fact_Orders[profit] < 0
)
```
- **Format:** Whole Number (`#,##0`)
- **Definition:** Count of product line items sold at negative margins.
- **Reconciled Value:** `1,871`

---

### `[Loss Item Share %]`
```dax
Loss Item Share % = 
DIVIDE ( [Loss Line Items], COUNTROWS ( Fact_Orders ), 0 )
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Proportion of total transaction line items resulting in a net loss.
- **Reconciled Value:** `18.72%`

---

### `[Loss Orders Count]`
```dax
Loss Orders Count = 
CALCULATE (
    DISTINCTCOUNT ( Fact_Orders[order_id] ),
    Fact_Orders[profit] < 0
)
```
- **Format:** Whole Number (`#,##0`)
- **Definition:** Count of customer orders containing at least one unprofitable line item.
- **Reconciled Value:** `1,318`

---

### `[Loss Order Share %]`
```dax
Loss Order Share % = 
DIVIDE ( [Loss Orders Count], [Distinct Orders], 0 )
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Proportion of unique orders impacted by negative-margin sales.
- **Reconciled Value:** `26.31%`

---

## 3. Discount Measures & Semantic Distinctions

### `[Net Sales-Weighted Discount Proxy %]`
```dax
Net Sales-Weighted Discount Proxy % = 
DIVIDE (
    SUMX ( Fact_Orders, Fact_Orders[sales] * Fact_Orders[discount] ),
    [Total Sales],
    0
)
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Revenue-weighted discount proxy. Note that because `sales` is already net of discounts, this weights discounts by realized net revenue.
- **Reconciled Value:** `14.04%`

---

### `[Simple Average Discount %]`
```dax
Simple Average Discount % = 
AVERAGE ( Fact_Orders[discount] )
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Unweighted arithmetic mean of transaction line-item discounts.
- **Reconciled Value:** `15.62%`

---

### `[Gross List Sales Estimate]`
```dax
Gross List Sales Estimate = 
SUMX (
    FILTER ( Fact_Orders, Fact_Orders[discount] < 1.0 ),
    DIVIDE ( Fact_Orders[sales], 1.0 - Fact_Orders[discount], 0 )
)
```
- **Format:** Currency (`$#,##0.00`)
- **Definition:** Estimated catalogue list price revenue prior to customer discounting.
- **Reconciled Value:** `$2,863,935.04`

---

### `[Gross Discount Concession %]`
```dax
Gross Discount Concession % = 
DIVIDE (
    [Gross List Sales Estimate] - [Total Sales],
    [Gross List Sales Estimate],
    0
)
```
- **Format:** Percentage (`0.0%`)
- **Definition:** True economic concession rate relative to full gross list price.
- **Reconciled Value:** `19.79%`

---

## 4. Time Intelligence & Year-over-Year (YoY) Growth

### `[Sales Prior Year]`
```dax
Sales Prior Year = 
CALCULATE (
    [Total Sales],
    SAMEPERIODLASTYEAR ( Dim_Date[Date] )
)
```
- **Format:** Currency (`$#,##0.00`)
- **Prerequisite:** `Dim_Date` marked as Date Table with contiguous dates.

---

### `[Sales YoY Growth %]`
```dax
Sales YoY Growth % = 
DIVIDE (
    [Total Sales] - [Sales Prior Year],
    [Sales Prior Year],
    0
)
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Year-over-year revenue expansion percentage.

---

### `[Profit Prior Year]`
```dax
Profit Prior Year = 
CALCULATE (
    [Total Profit],
    SAMEPERIODLASTYEAR ( Dim_Date[Date] )
)
```
- **Format:** Currency (`$#,##0.00`)

---

### `[Profit YoY Growth %]`
```dax
Profit YoY Growth % = 
DIVIDE (
    [Total Profit] - [Profit Prior Year],
    [Profit Prior Year],
    0
)
```
- **Format:** Percentage (`0.0%`)
- **Definition:** Year-over-year bottom-line profit growth percentage.

---

### `[Sales YTD]`
```dax
Sales YTD = 
TOTALYTD ( [Total Sales], Dim_Date[Date] )
```
- **Format:** Currency (`$#,##0.00`)
