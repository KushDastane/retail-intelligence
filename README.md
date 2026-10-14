# Retail Intelligence: Sales & Profitability Analytics

[![Python](https://img.shields.io/badge/Python-3.14.2-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-3.50.4-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-41%20Passed-brightgreen.svg)]()
[![Excel](https://img.shields.io/badge/Excel-Formula--Driven%20Model-green.svg)]()
[![PowerBI](https://img.shields.io/badge/PowerBI-Star%20Schema%20DAX-yellow.svg)]()

A reproducible, portfolio-grade retail analytics project engineered to answer a fundamental commercial dilemma:

> **"How can a retail business improve profitability without sacrificing sales growth?"**

---

## 1. Executive Summary & Core KPIs

Analyzing **9,994 transactional line items** across US commercial operations reveals that the business generated **$2,297,200.86 in net sales** and **$286,397.02 in net profit** (**12.47% overall profit margin**). However, profitability is severely diluted by internal value destruction:

| Metric | Verified Empirical Value | Analytical Definition & Measurement Rule |
| :--- | :--- | :--- |
| **Total Net Sales** | **$2,297,200.86** | Realized post-discount customer revenue ($\sum \text{Sales}$). |
| **Gross Catalogue List Sales** | **$2,863,935.04** | Estimated undiscounted list price value ($\sum \frac{\text{Sales}}{1 - \text{Discount}}$). |
| **Gross Discount Concession** | **$566,734.18 (19.79%)** | True economic concession forfeited against catalogue list price. |
| **Net Sales-Weighted Discount**| **14.04%** | Net-revenue-weighted discount proxy ($\frac{\sum \text{Sales} \times \text{Discount}}{\sum \text{Sales}}$). |
| **Simple Average Discount** | **15.62%** | Unweighted arithmetic mean of line-item discounts. |
| **Total Net Profit** | **$286,397.02** | Net financial earnings after product costs and discounting. |
| **Overall Profit Margin** | **12.47%** | Portfolio ratio: $\frac{\sum \text{Profit}}{\sum \text{Sales}} \times 100\%$ (Simpson's paradox prevention). |
| **Distinct Order Count** | **5,009** | Unique order baskets (using `COUNT(DISTINCT order_id)`). |
| **Total Unique Customers** | **793** | Customer accounts across Consumer, Corporate, and Home Office. |
| **Average Order Value (AOV)** | **$458.61** | Average revenue per distinct order basket ($\frac{\text{Sales}}{\text{Orders}}$). |
| **Total Loss Dollars** | **-$156,131.29** | **The Profit Drain:** Cumulative negative profit generated on loss items. |
| **Loss Line-Item Share** | **18.72%** | 1,871 out of 9,994 transactions were sold at a financial loss. |
| **Loss-Impacted Orders** | **26.31%** | 1,318 out of 5,009 customer orders contained at least one loss item. |

---

## 2. Key Empirical Findings (With Disclosures)

All figures below are derived from verified Python and SQLite analytical queries and cross-validated against visualizations in `reports/figures/`.

### A. Monthly Seasonality vs. Margin Dilution
- **Holiday Volume Surges:** Sales exhibit clear seasonal spikes every Q4 (November/December), peaking at **$118,447.82 in November 2017**.
- **Promotional Margin Compression:** During the November 2017 peak, net profit margin compressed to **8.18%** (compared to the 12.47% annual benchmark), confirming that volume was acquired through heavy promotional margin concessions.

### B. Category Profit Engines vs. Chronic Loss Leaders
- **Technology Drives Earnings:** Technology delivered **$145,454.95 in profit** (17.40% margin), led by **Copiers** (+$55.6K, 37.2% margin) and **Phones** (+$44.5K, 13.5% margin).
- **Furniture Margin Dilution:** Furniture generated only **$18,451.27 in profit** on **$741,999.80 in sales** (**2.49% overall margin**).
- **Unprofitable Subcategories:**
  - **Tables:** **-$17,725.48 net loss** (-8.56% margin) on $207.0K sales (accumulating -$32.4K in gross losses).
  - **Bookcases:** **-$3,472.56 net loss** (-3.02% margin) on $114.9K sales.
  - **Supplies:** **-$1,189.10 net loss** (-2.55% margin) on $46.7K sales.

### C. The 20% Discount Breakeven Cliff
- **Observed Pattern:** In this retailer's operating cost structure, transactions discounted up to 20% remain healthy (+11.6% to +29.8% margin).
- **The Margin Cliff:** Past 20% discount, aggregate profitability collapses:
  - **20.1% - 30% discount:** **-10.05% margin** (74.0% of items unprofitable, -$13.4K loss).
  - **30.1% - 50% discount:** **-24.80% margin** (89.7% of items unprofitable, -$50.3K loss).
  - **> 50% discount:** **-119.17% margin** (100% of items unprofitable, losing $1.19 per $1.00 net sales).
- *Qualification:* Total negative profit on lines discounted >20% was **-$135,376.06**. Capping discounts at 20% would protect margins, but recoverable profit in live retail depends on customer elasticity and basket retention.

### D. Geographic Loss Centers
- **West Region Leads:** Delivers **$108,418.45 in profit** (**14.94% margin**).
- **Central Region Lags:** Produces only **$39,706.36 in profit** (**7.92% margin**), dragged down by heavy discounting in **Texas** (-$25.7K loss, 37.0% avg discount) and **Illinois** (-$12.6K loss, 38.9% avg discount).
- **East Region Drains:** **Pennsylvania** (-$15.6K loss, 32.9% avg discount) and **Ohio** (-$17.0K loss, 43.2% avg discount).

### E. Customer Value Concentration (Pareto Decile Distribution)
- **Top 20% (Deciles 1 & 2):** 160 customers generate **$234,568.47 in profit**, accounting for **81.90% of company earnings**.
- **Decile 10 Anomaly:** The bottom 10% of customers (79 accounts) generate **$278,279.04 in revenue** (high volume), but incur **-$65,753.64 in cumulative net losses** (margin: -23.63%) due to average discounts exceeding 37%.

---

## 3. Visualizations Gallery

All charts are dynamically generated at 300 DPI by `src/visualization.py`:

| Visual Focus | Preview / File Link | Key Takeaway |
| :--- | :--- | :--- |
| **Monthly Trends** | [01_monthly_sales_profit_trend.png](reports/figures/01_monthly_sales_profit_trend.png) | Q4 holiday volume surges pair with promotional margin compression. |
| **Subcategories** | [02_category_subcategory_profitability.png](reports/figures/02_category_subcategory_profitability.png) | Technology generates 50.8% of profit; Tables and Bookcases destroy value. |
| **Discount Cliff** | [03_discount_band_analysis.png](reports/figures/03_discount_band_analysis.png) | Margins collapse past 20% discount (with sample sizes disclosed). |
| **Regional Performance**| [04_regional_state_profitability.png](reports/figures/04_regional_state_profitability.png) | Central region margin suppressed to 7.9% by Texas and Illinois losses. |
| **Customer Deciles** | [05_customer_decile_pareto.png](reports/figures/05_customer_decile_pareto.png) | Top 20% accounts drive 81.9% profit; Decile 10 generates $278K sales at -$65.8K loss. |

---

## 4. Evidence-Backed Strategic Recommendations

| Strategic Pillar | Empirical Evidence | Commercial Action | Business Impact |
| :--- | :--- | :--- | :--- |
| **1. Promotional Guardrails** | Discounts >20% suffer aggregate negative margins (-10% to -119%), leaking -$135K in cumulative losses. | Cap discretionary sales rep discounts at 20%; require Regional VP approval for larger concessions. | Restrains margin decay while keeping standard promotional elasticity intact. |
| **2. Loss-Leader Bundling** | Tables (-$17.7K) and Bookcases (-$3.5K) have >31% failure rates. | Restructure Tables/Bookcases as bundle-only purchases with high-margin Chairs or Technology. | Preserves basket halo effect while stopping standalone negative-margin sales. |
| **3. Account Margin Floors** | Customer Decile 10 buys $278K at -$65.8K net loss (avg discount 37.1%). | Implement quarterly volume-rebates conditioned on accounts maintaining a minimum 10% basket margin. | Converts high-volume loss accounts into profitable contracts without losing accounts. |
| **4. Regional Autonomy Reform** | Texas (-$25.7K), Ohio (-$17.0K), and Illinois (-$12.6K) have >37% average discounts. | Audit local commercial sales discretion in Central and East territories to halt localized price wars. | Elevates Central margin from 7.9% toward the company benchmark of 12.5%. |

---

## 5. Technology Stack & Repository Architecture

```text
retail-intelligence/
├── .gitignore                      # Excludes .venv, raw/clean data, and database artifacts
├── README.md                       # Comprehensive project landing page & audit guide
├── requirements.txt                # Pinned dependencies compatible with Python 3.14+
├── data/
│   ├── raw/                        # Preserved original dataset (sample_superstore.csv)
│   └── processed/                  # Cleaned tabular output (retail_orders_clean.csv)
├── src/
│   ├── config.py                   # Central paths, schema mappings, and metadata
│   ├── data/
│   │   ├── download.py             # Deterministic download with SHA-256 verification
│   │   ├── clean.py                # Type casting, date parsing, and feature engineering
│   │   └── validate.py             # Defensive integrity suite (nulls, ranges, temporal checks)
│   ├── db.py                       # SQLite database manager & migration engine
│   ├── metrics.py                  # Formal metrics, weighted discount proxy, and loss footprint
│   └── visualization.py            # Publication-grade Matplotlib/Seaborn charting engine
├── sql/
│   ├── 01_schema.sql               # SQLite DDL with CHECK constraints and 7 indexes
│   ├── 02_kpi_summary.sql          # Executive scorecard & loss footprint
│   ├── 03_category_profitability.sql# Subcategory CTE and window rankings
│   ├── 04_regional_segment.sql     # Region x Segment matrix with window profit shares
│   ├── 05_discount_impact.sql      # Discount tier decay and cliff detection with LAG()
│   └── 06_customer_value.sql       # Customer decile Pareto analysis with NTILE(10)
├── notebooks/
│   └── sales_profitability_eda.ipynb # Reproducible Jupyter Notebook walkthrough
├── excel/
│   ├── generate_excel_model.py     # Automation script building formula-driven model
│   └── retail_sales_analysis.xlsx  # Multi-tab workbook (KPI Dashboard, Orders, Matrices)
├── powerbi/
│   ├── data_model.md               # Star Schema dimensional modeling specification
│   ├── dax_measures.md             # Reconciled DAX measures library
│   ├── powerbi_guide.md            # Step-by-step 3-page interactive dashboard build guide
│   └── retail_theme.json           # Ready-to-import Power BI palette configuration
├── reports/
│   ├── figures/                    # 5 exported high-resolution PNG charts (300 DPI)
│   ├── executive_summary.md        # Comprehensive business briefing
│   └── interview_guide.md          # 10 technical & behavioral interview defense Q&As
└── tests/
    ├── test_metrics.py             # 8 unit tests for formulas & order deduplication
    ├── test_validation.py          # 11 unit & integration tests for data pipeline
    ├── test_reconciliation.py      # 9 tests asserting Python == SQLite SQL metrics
    ├── test_visualization.py       # 7 tests for chart data transformations & PNG files
    └── test_excel.py               # 6 tests for workbook structure, rows, and formulas
```

---

## 6. Setup & Execution Guide (Windows / Python 3.14)

### Prerequisites
- Python 3.14.2 installed.
- PowerShell or Command Prompt.

### Step 1: Virtual Environment & Dependencies
> **Windows Security Note:** On Windows systems with Application Control policies, invoking `.venv\Scripts\pip.exe` directly may be restricted. Always execute tooling through the Python interpreter using `python -m <module>`.

```powershell
# Activate existing environment or create one
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 2: Download & Clean Dataset
```powershell
# 1. Deterministic download with SHA-256 verification
.\.venv\Scripts\python.exe -m src.data.download

# 2. Run data cleaning, postal code standardization, and feature engineering
.\.venv\Scripts\python.exe -m src.data.clean
```

### Step 3: Initialize SQLite Database & Ingest Data
```powershell
.\.venv\Scripts\python.exe -m src.db
```

### Step 4: Generate Publication-Grade Visualizations
```powershell
.\.venv\Scripts\python.exe -m src.visualization
```

### Step 5: Generate the Excel Analysis Model
```powershell
.\.venv\Scripts\python.exe excel/generate_excel_model.py
```

### Step 6: Run Complete Automated Test Suite (41 Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 7. Power BI Implementation Note

- **PBIX Status:** Power BI `.pbix` files are proprietary binary packages containing compiled Mashup packages and VertiPaq internal databases; creating a `.pbix` programmatically without the Power BI Desktop application GUI running can produce corrupt files.
- **Implementation Assets:** We provide [powerbi/data_model.md](powerbi/data_model.md), [powerbi/dax_measures.md](powerbi/dax_measures.md), [powerbi/powerbi_guide.md](powerbi/powerbi_guide.md), and [powerbi/retail_theme.json](powerbi/retail_theme.json) for direct assembly in Power BI Desktop in under 10 minutes.

---

## 8. Dataset Provenance, Licence & Limitations

- **Dataset:** Tableau Sample - Superstore.
- **Source:** Hosted educational clone repository (`sumit0072/Superstore-Data-Analysis`).
- **Licence & Usage:** Public domain educational benchmark distributed historically for analytics training.
- **Limitations:**
  1. Synthetic, demonstration transactional data covering US retail orders from 2014 to 2017.
  2. Lacks supply chain carrying costs, warehouse storage fees, and customer acquisition costs (CAC).
  3. Price elasticity cannot be estimated directly without historical price testing experiments.

---

## 9. Interview Defense Guide

For technical defense against questions regarding Simpson's paradox, SQL window functions, discount semantics, and Star Schema modeling, refer to:
👉 **[reports/interview_guide.md](reports/interview_guide.md)**
