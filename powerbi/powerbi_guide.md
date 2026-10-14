# Power BI Interactive Dashboard Build Guide: Retail Intelligence

This document provides a comprehensive, step-by-step implementation guide to assemble the portfolio-grade interactive Power BI report for **Retail Intelligence: Sales & Profitability Analytics**.

---

## 1. Environment & Data Ingestion Setup

### Step 1: Launch Power BI Desktop & Load Clean Data
1. Launch **Microsoft Power BI Desktop** (installed at `PBIDesktopStore.exe` / WindowsApps on your machine).
2. Click **Get Data** $\rightarrow$ **Text/CSV**.
3. Navigate to and select:  
   `c:\Users\Yogini Dastane\Documents\retail-intelligence\data\processed\retail_orders_clean.csv`
4. In the preview window, confirm delimiter is **Comma** and character encoding is **65001: UTF-8**.
5. Click **Transform Data** to open Power Query Editor:
   - Rename query from `retail_orders_clean` to `Fact_Orders`.
   - Verify `order_date` and `ship_date` are typed as **Date**.
   - Verify `sales`, `profit`, `discount`, `unit_price`, and `line_profit_margin` are typed as **Decimal Number**.
   - Verify `quantity`, `shipping_days`, `is_profitable`, and `is_loss` are typed as **Whole Number**.
6. Click **Close & Apply**.

---

## 2. Building the Star Schema Dimensions

In Power BI Desktop, navigate to **Modeling** $\rightarrow$ **New Table** to create each dimension:

### Step 1: Create `Dim_Date`
```dax
Dim_Date = 
ADDCOLUMNS (
    CALENDAR ( DATE ( 2014, 1, 1 ), DATE ( 2017, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & FORMAT ( [Date], "Q" ),
    "YearQuarter", YEAR ( [Date] ) & "-Q" & FORMAT ( [Date], "Q" ),
    "MonthNum", MONTH ( [Date] ),
    "MonthName", FORMAT ( [Date], "mmmm" ),
    "MonthYear", FORMAT ( [Date], "yyyy-mm" ),
    "DayOfWeek", FORMAT ( [Date], "dddd" )
)
```
- In Data View, select `MonthYear` and click **Sort by column** $\rightarrow$ select `Date`.
- Right-click `Dim_Date` table $\rightarrow$ **Mark as Date Table** $\rightarrow$ select `Date` column.

### Step 2: Create Entity Dimensions
Create the remaining dimension tables via **Modeling** $\rightarrow$ **New Table**:

```dax
Dim_Product = 
SUMMARIZE (
    Fact_Orders,
    Fact_Orders[product_id],
    Fact_Orders[product_name],
    Fact_Orders[category],
    Fact_Orders[sub_category]
)
```

```dax
Dim_Customer = 
SUMMARIZE (
    Fact_Orders,
    Fact_Orders[customer_id],
    Fact_Orders[customer_name],
    Fact_Orders[segment]
)
```

```dax
Dim_Geography = 
SUMMARIZE (
    Fact_Orders,
    Fact_Orders[postal_code],
    Fact_Orders[city],
    Fact_Orders[state],
    Fact_Orders[region],
    Fact_Orders[country]
)
```

### Step 3: Configure Relationships in Model View
Navigate to **Model View** and drag-and-drop to establish active single-direction `1:*` relationships:
- `Dim_Date[Date]` ($1$) $\rightarrow$ `Fact_Orders[order_date]` ($*$)
- `Dim_Product[product_id]` ($1$) $\rightarrow$ `Fact_Orders[product_id]` ($*$)
- `Dim_Customer[customer_id]` ($1$) $\rightarrow$ `Fact_Orders[customer_id]` ($*$)
- `Dim_Geography[postal_code]` ($1$) $\rightarrow$ `Fact_Orders[postal_code]` ($*$)

---

## 3. Creating the Measures Table

1. On the **Home** ribbon, click **Enter Data**.
2. Name the table `_Measures` and column `Column1`, then click **Load**.
3. Create all DAX measures documented in [powerbi/dax_measures.md](file:///c:/Users/Yogini%20Dastane/Documents/retail-intelligence/powerbi/dax_measures.md):
   - `Total Sales`
   - `Total Profit`
   - `Profit Margin %`
   - `Distinct Orders`
   - `Distinct Customers`
   - `Average Order Value`
   - `Total Loss Dollars`
   - `Loss Item Share %`
   - `Net Sales-Weighted Discount Proxy %`
   - `Sales Prior Year`
   - `Sales YoY Growth %`
4. Delete the placeholder `Column1` from `_Measures` so the table icon turns into a calculator icon.

---

## 4. Visual Layout Specifications (3 Interactive Pages)

### Canvas Configuration
- **Page Dimensions:** 16:9 Widescreen (1280 x 720 px)
- **Background Color:** Off-white / Slate `#F8FAFC`
- **Color Palette:**
  - Primary Dark / Text: `#1E293B`
  - Accent / Profitable: `#0F766E` (Teal)
  - Volume / Secondary: `#0284C7` (Sky Blue)
  - Negative Profit / Alert: `#E11D48` (Rose Red)

---

### Page 1: Executive Overview

**Goal:** Provide senior leadership with a consolidated operational view of sales, margins, volume, and seasonal patterns.

1. **Header Banner (Top, Y: 10, H: 45):**
   - Text Box: **"Retail Intelligence — Executive Performance Overview"** (Font: Segoe UI, 18pt, Bold, Color: `#1E293B`).
   - Subtitle: *"Performance tracking across 5,009 customer orders (2014-2017)"*.
2. **Top Slicers (Y: 65, H: 45):**
   - **Date Slicer:** `Dim_Date[Date]` (Type: Between slider).
   - **Region Slicer:** `Dim_Geography[region]` (Type: Tile / Horizontal pills).
   - **Segment Slicer:** `Dim_Customer[segment]` (Type: Dropdown).
3. **KPI Scorecard Cards (Y: 120, H: 75, 6 Equal Width Cards):**
   - Card 1: `[Total Sales]` (Display units: `$2.30M`)
   - Card 2: `[Total Profit]` (Display units: `$286.4K`)
   - Card 3: `[Profit Margin %]` (Display units: `12.5%`)
   - Card 4: `[Distinct Orders]` (Display units: `5,009`)
   - Card 5: `[Average Order Value]` (Display units: `$458.61`)
   - Card 6: `[Loss Item Share %]` (Display units: `18.7%`, Callout color: `#E11D48`)
4. **Visual 1 (Left Panel, W: 780, H: 460): Line and Clustered Column Chart**
   - **Title:** "Monthly Net Sales & Profit Trajectory (with Prior Year Benchmark)"
   - **Shared Axis:** `Dim_Date[YearMonth]`
   - **Column Values:** `[Total Sales]`
   - **Line Values:** `[Total Profit]`
   - **Secondary Line:** `[Sales Prior Year]` (Dashed line)
   - **Formatting:** Columns in Sky Blue (`#0284C7`), Line in Teal (`#0F766E`).
5. **Visual 2 (Right Panel, W: 450, H: 460): Clustered Bar Chart**
   - **Title:** "Regional Sales & Profit Margin Performance"
   - **Y-Axis:** `Dim_Geography[region]` (Sorted by `[Total Profit]` descending)
   - **X-Axis:** `[Total Profit]`
   - **Tooltip:** `[Total Sales]`, `[Profit Margin %]`, `[Distinct Orders]`
   - **Conditional Formatting:** Color bars based on `[Profit Margin %]` (> 10% = Teal, < 10% = Amber/Rose).

---

### Page 2: Product Profitability & Loss Leaders

**Goal:** Answer which categories and subcategories drive profitability and identify chronic loss leaders.

1. **Header & Slicers (Top):**
   - Slicers: `Dim_Product[category]` (Dropdown), `Dim_Date[Year]` (Pills).
2. **Visual 1 (Left Panel, W: 680, H: 540): Clustered Horizontal Bar Chart**
   - **Title:** "Subcategory Net Profit Ranking & Loss Leaders"
   - **Y-Axis:** `Dim_Product[sub_category]` (Sorted by `[Total Profit]` descending)
   - **X-Axis:** `[Total Profit]`
   - **Data Labels:** ON (Format: Currency `$#,##0`)
   - **Conditional Formatting:** Rule on `[Total Profit]`:
     - `< 0`: Soft Red / Rose (`#E11D48`) $\rightarrow$ immediately flags **Tables**, **Bookcases**, and **Supplies**.
     - `> 0`: Deep Teal (`#0F766E`).
3. **Visual 2 (Top Right, W: 550, H: 260): Scatter Plot (Portfolio Matrix)**
   - **Title:** "Subcategory Margin vs Sales Volume"
   - **X-Axis:** `[Total Sales]`
   - **Y-Axis:** `[Profit Margin %]`
   - **Details:** `Dim_Product[sub_category]`
   - **Size:** `[Total Loss Dollars]` (Absolute value)
   - **Reference Line:** Horizontal constant line at `0.0%` margin (Breakeven boundary).
4. **Visual 3 (Bottom Right, W: 550, H: 260): Ranked Loss Products Table**
   - **Title:** "Top 10 Most Unprofitable Product SKUs"
   - **Columns:** `Dim_Product[product_name]`, `Dim_Product[sub_category]`, `[Total Sales]`, `[Total Profit]`, `[Profit Margin %]`
   - **Filter:** Visual-level Top N filter $\rightarrow$ Bottom 10 by `[Total Profit]`.

---

### Page 3: Discount Policy & Customer Segmentation

**Goal:** Provide commercial governance evidence: evaluate discount thresholds and identify high-volume unprofitable customer accounts.

1. **Header & Slicers (Top):**
   - Slicers: `Fact_Orders[discount_band]` (Multi-select), `Dim_Geography[region]`.
2. **Visual 1 (Left Panel, W: 620, H: 540): Line and Clustered Column Chart**
   - **Title:** "The 20% Discount Breakeven Cliff: Volume vs Margin Decay"
   - **Shared Axis:** `Fact_Orders[discount_band]`
   - **Column Values:** `COUNTROWS(Fact_Orders)` (Transaction sample size $n$)
   - **Line Values:** `[Profit Margin %]`
   - **Data Labels:** ON (Format: `0.0%` on line)
   - **Reference Line:** Horizontal line at `0.0%` margin.
   - **Insight Callout:** Annotates that beyond 20% discount, portfolio margin collapses from +11.6% to -10.1% and -119.2%.
3. **Visual 2 (Top Right, W: 610, H: 260): Customer Decile Bar Chart**
   - **Title:** "Customer Decile Economics: Net Sales vs Net Profit"
   - **Axis:** `Customer Decile` (1 to 10)
   - **Values:** `[Total Sales]` (Sky Blue), `[Total Profit]` (Teal/Rose)
   - **Insight:** Highlights Decile 10 producing $278K sales but -$65.8K in losses.
4. **Visual 3 (Bottom Right, W: 610, H: 260): Chronic Loss Accounts Table**
   - **Title:** "High-Volume Unprofitable Customer Accounts (Decile 10)"
   - **Columns:** `Dim_Customer[customer_name]`, `Dim_Customer[segment]`, `Dim_Geography[state]`, `[Total Sales]`, `[Total Profit]`, `[Net Sales-Weighted Discount Proxy %]`
   - **Sort:** `[Total Profit]` ascending (worst loss accounts first).

---

## 5. Automation & Theme Configuration

To automatically apply our modern, restrained styling palette to Power BI Desktop, save the following JSON snippet as `retail_theme.json` and import via **View** $\rightarrow$ **Themes** $\rightarrow$ **Browse for themes**:

```json
{
  "name": "RetailIntelligenceTheme",
  "dataColors": [
    "#0F766E",
    "#0284C7",
    "#E11D48",
    "#F59E0B",
    "#64748B",
    "#475569",
    "#059669",
    "#7C3AED"
  ],
  "background": "#F8FAFC",
  "foreground": "#1E293B",
  "tableAccent": "#0F766E",
  "visualStyles": {
    "*": {
      "*": {
        "title": [
          {
            "fontColor": { "solid": { "color": "#1E293B" } },
            "fontSize": 12,
            "fontFamily": "Segoe UI"
          }
        ],
        "grid": [
          {
            "gridVertical": false,
            "gridHorizontal": true,
            "gridHorizontalColor": { "solid": { "color": "#E2E8F0" } }
          }
        ]
      }
    }
  }
}
```

---

## 6. Implementation Notes on `.pbix` Generation

Power BI Desktop files (`.pbix`) are proprietary, signed binary zip packages containing embedded mashup packages (`DataMashup`), SQLite/VertiPaq schemas (`DataModel`), and encrypted visual layouts. Constructing raw binary `.pbix` files outside the Power BI Desktop application GUI can produce corrupted containers.

Because Power BI Desktop is installed locally on your system, the recommended workflow is:
1. Open Power BI Desktop.
2. Follow the 10-minute setup above using `data/processed/retail_orders_clean.csv`.
3. Import `retail_theme.json`.
4. Copy-paste the DAX measures from `powerbi/dax_measures.md`.
5. Save the report directly as `powerbi/retail_intelligence.pbix`.
