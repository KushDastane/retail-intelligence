
"""Automated cross-platform reconciliation tests.

Validates that metrics calculated in Python and queries executed in SQLite
match exactly, verifying architectural integrity across analytical layers.
"""

import math
import pandas as pd
import pytest

from src.config import DATABASE_PATH, PROCESSED_DATA_FILE, SQL_DIR
from src.db import execute_sql_query, get_connection
from src.metrics import executive_kpi_summary


@pytest.fixture(scope="module")
def processed_df() -> pd.DataFrame:
    """Fixture providing the processed retail DataFrame."""
    if not PROCESSED_DATA_FILE.exists():
        pytest.skip("Processed dataset not found.")
    return pd.read_csv(PROCESSED_DATA_FILE)


def test_database_table_record_count():
    """Verify that the SQLite retail_orders table is loaded with all 9,994 rows."""
    if not DATABASE_PATH.exists():
        pytest.skip("Database retail.db not built yet.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM retail_orders;")
        count = cursor.fetchone()[0]

    assert count == 9994


@pytest.mark.parametrize(
    "sql_filename, min_rows",
    [
        ("02_kpi_summary.sql", 1),
        ("03_category_profitability.sql", 17),  # 17 subcategories
        ("04_regional_segment.sql", 12),       # 4 regions x 3 segments
        ("05_discount_impact.sql", 6),          # 6 discount bands
        ("06_customer_value.sql", 10),          # 10 deciles
    ],
)
def test_all_sql_files_execute_successfully(sql_filename, min_rows):
    """Verify each analytical SQL file executes without error and yields expected rows."""
    sql_path = SQL_DIR / sql_filename
    assert sql_path.exists(), f"SQL script {sql_filename} is missing."

    df_result = execute_sql_query(sql_path)
    assert not df_result.empty
    assert len(df_result) >= min_rows


def test_kpi_reconciliation_python_vs_sql(processed_df):
    """Assert Python metric scorecard equals SQLite SQL scorecard to 2 decimal places."""
    py_kpis = executive_kpi_summary(processed_df)
    sql_kpis = execute_sql_query(SQL_DIR / "02_kpi_summary.sql").to_dict(orient="records")[0]

    # Reconcile Core KPIs
    assert math.isclose(py_kpis["total_sales"], sql_kpis["total_sales"], abs_tol=0.01)
    assert math.isclose(py_kpis["total_profit"], sql_kpis["total_profit"], abs_tol=0.01)
    assert math.isclose(py_kpis["profit_margin_pct"], sql_kpis["profit_margin_pct"], abs_tol=0.01)
    assert py_kpis["total_orders"] == sql_kpis["total_orders"]
    assert py_kpis["total_customers"] == sql_kpis["total_customers"]
    assert py_kpis["total_units"] == sql_kpis["total_units_sold"]
    assert math.isclose(py_kpis["average_order_value"], sql_kpis["avg_order_value"], abs_tol=0.01)

    # Reconcile Loss Footprint
    assert math.isclose(py_kpis["total_loss_dollars"], sql_kpis["total_loss_dollars"], abs_tol=0.01)
    assert py_kpis["loss_item_share_pct"] == sql_kpis["loss_item_share_pct"]
    assert py_kpis["loss_order_share_pct"] == sql_kpis["loss_order_share_pct"]

    # Reconcile Discount Rates
    assert math.isclose(py_kpis["weighted_discount_pct"], sql_kpis["net_sales_weighted_discount_pct"], abs_tol=0.01)
    assert math.isclose(py_kpis["simple_discount_pct"], sql_kpis["simple_avg_discount_pct"], abs_tol=0.01)


def test_category_profit_sum_equals_overall_profit():
    """Verify that sum of subcategory profits equals overall company profit."""
    df_cat = execute_sql_query(SQL_DIR / "03_category_profitability.sql")
    sum_subcat_profit = round(float(df_cat["total_profit"].sum()), 2)
    assert math.isclose(sum_subcat_profit, 286397.02, abs_tol=0.05)


def test_discount_tiers_total_line_items_equal_total_dataset():
    """Verify all 9,994 line items are accounted for across discount bands."""
    df_discount = execute_sql_query(SQL_DIR / "05_discount_impact.sql")
    assert int(df_discount["total_line_items"].sum()) == 9994


def test_customer_deciles_account_for_all_customers():
    """Verify customer deciles sum to exactly 793 distinct customers."""
    df_cust = execute_sql_query(SQL_DIR / "06_customer_value.sql")
    assert int(df_cust["customer_count"].sum()) == 793
