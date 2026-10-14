"""Central configuration for retail-intelligence analytics pipeline.

All paths, dataset source metadata, schema definitions, and analytical constants
are defined here to ensure complete reproducibility across machines.
"""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# File and Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_DATA_FILE = RAW_DATA_DIR / "sample_superstore.csv"
PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / "retail_orders_clean.csv"

SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
EXCEL_DIR = PROJECT_ROOT / "excel"
POWERBI_DIR = PROJECT_ROOT / "powerbi"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DATABASE_PATH = PROJECT_ROOT / "retail.db"

# Dataset Source Metadata
# Dataset: Tableau Sample - Superstore (Educational / Training Benchmark Dataset)
# Source: Hosted clone on GitHub repository (sumit0072/Superstore-Data-Analysis)
# Usage & Licence: Public domain / educational benchmarking dataset derived from Tableau's
# standard demonstration sample data. Distributed freely for analytics training and portfolios;
# contains synthetic US retail transactional records (2014-2017).
DATASET_SOURCE_URL = (
    "https://raw.githubusercontent.com/sumit0072/Superstore-Data-Analysis/main/Sample%20-%20Superstore.csv"
)
DATASET_ENCODING = "windows-1252"
DATASET_EXPECTED_ROWS = 9994
DATASET_EXPECTED_COLUMNS = 21

# Mapping from raw CSV headers to clean snake_case column names
COLUMN_MAPPING = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}

# Critical non-null columns
MANDATORY_COLUMNS = [
    "row_id",
    "order_id",
    "order_date",
    "ship_date",
    "customer_id",
    "category",
    "sub_category",
    "sales",
    "quantity",
    "discount",
    "profit",
]

# Standard Discount Bands for Retail Analysis
DISCOUNT_BINS = [-0.001, 0.000, 0.100, 0.200, 0.300, 0.500, 1.000]
DISCOUNT_LABELS = [
    "0% (No Discount)",
    "0.1% - 10%",
    "10.1% - 20%",
    "20.1% - 30%",
    "30.1% - 50%",
    "> 50% (Deep Discount)",
]
