"""Unit tests for analytical metric calculations and KPI logic.

Tests critical business measurement properties:
1. Avoid double-counting orders across multi-item transactions.
2. Ensure overall profit margin aggregates before dividing (avoiding Simpson's paradox in margins).
3. Distinguish sales-weighted discount from simple average discount.
4. Defensively handle zero sales and empty DataFrames.
"""

import pandas as pd
import pytest

from src.metrics import (
    average_order_value,
    executive_kpi_summary,
    loss_analysis_summary,
    overall_profit_margin,
    sales_weighted_discount,
    simple_average_discount,
    total_distinct_customers,
    total_distinct_orders,
    total_profit,
    total_sales,
)


@pytest.fixture
def multi_item_order_df() -> pd.DataFrame:
    """Fixture with multi-item orders and varying margins and discounts."""
    return pd.DataFrame(
        {
            "row_id": [1, 2, 3, 4],
            "order_id": ["ORD-101", "ORD-101", "ORD-102", "ORD-103"],
            "customer_id": ["CUST-1", "CUST-1", "CUST-2", "CUST-1"],
            "sales": [10.0, 1000.0, 200.0, 300.0],
            "profit": [5.0, -100.0, 40.0, 60.0],
            "quantity": [1, 5, 2, 3],
            "discount": [0.80, 0.00, 0.10, 0.05],
        }
    )


def test_total_distinct_orders_avoids_line_item_count(multi_item_order_df):
    """Verify distinct order count equals 3, NOT 4 (ORD-101 has 2 line items)."""
    assert len(multi_item_order_df) == 4
    assert total_distinct_orders(multi_item_order_df) == 3


def test_total_distinct_customers(multi_item_order_df):
    """Verify distinct customer count equals 2 (CUST-1 has multiple orders)."""
    assert total_distinct_customers(multi_item_order_df) == 2


def test_overall_margin_prevents_arithmetic_mean_distortion():
    """Verify that overall margin aggregates numerator and denominator before dividing.

    Simpson's paradox illustration:
    Row 1: Sales $10, Profit $5 -> Line margin = +50%
    Row 2: Sales $1,000, Profit -$100 -> Line margin = -10%

    Arithmetic mean of line margins = (+50% - 10%) / 2 = +20% (falsely suggests profitability!)
    True portfolio margin = ($5 - $100) / ($10 + $1,000) = -$95 / $1,010 = -9.4059% (loss-making)
    """
    df = pd.DataFrame(
        {
            "sales": [10.0, 1000.0],
            "profit": [5.0, -100.0],
        }
    )
    # Overall margin must be negative (-9.41%)
    true_margin = overall_profit_margin(df)
    assert true_margin < 0
    assert round(true_margin, 2) == -9.41


def test_sales_weighted_discount_vs_simple_average():
    """Verify sales-weighted discount correctly reflects revenue exposure.

    Row 1: Sales $10, Discount 80% (0.80) -> Heavy discount on negligible revenue ($8 concession)
    Row 2: Sales $1,000, Discount 0% (0.00) -> Zero discount on main revenue ($0 concession)

    Simple average = (80% + 0%) / 2 = 40.0% (heavily overstated)
    Sales-weighted discount = $8 / $1,010 = 0.792% (true economic discount rate)
    """
    df = pd.DataFrame(
        {
            "sales": [10.0, 1000.0],
            "discount": [0.80, 0.00],
        }
    )
    simple = simple_average_discount(df)
    weighted = sales_weighted_discount(df)

    assert simple == 40.0
    assert round(weighted, 2) == 0.79


def test_average_order_value(multi_item_order_df):
    """Verify AOV = total sales / distinct orders."""
    # Total sales = 10 + 1000 + 200 + 300 = 1510.0
    # Distinct orders = 3
    # AOV = 1510 / 3 = 503.33
    aov = average_order_value(multi_item_order_df)
    assert aov == 503.33


def test_loss_analysis_summary(multi_item_order_df):
    """Verify loss analysis correctly aggregates negative profit items and affected orders."""
    loss_stats = loss_analysis_summary(multi_item_order_df)

    # 1 line item is negative (Row 2: -$100)
    assert loss_stats["loss_line_items"] == 1
    assert loss_stats["loss_item_share_pct"] == 25.0  # 1 out of 4 items = 25%
    assert loss_stats["total_loss_dollars"] == -100.0
    assert loss_stats["loss_orders_count"] == 1
    assert round(loss_stats["loss_order_share_pct"], 2) == 33.33  # 1 of 3 orders = 33.33%


def test_zero_sales_safe_handling():
    """Verify that zero sales DataFrame does not trigger ZeroDivisionError."""
    df_empty = pd.DataFrame({"sales": [], "profit": [], "order_id": []})
    assert total_sales(df_empty) == 0.0
    assert total_profit(df_empty) == 0.0
    assert overall_profit_margin(df_empty) == 0.0
    assert average_order_value(df_empty) == 0.0
    assert sales_weighted_discount(df_empty) == 0.0


def test_executive_kpi_summary_keys(multi_item_order_df):
    """Verify that executive scorecard contains all expected metrics."""
    scorecard = executive_kpi_summary(multi_item_order_df)
    expected_keys = [
        "total_sales",
        "total_profit",
        "profit_margin_pct",
        "total_orders",
        "total_customers",
        "total_units",
        "average_order_value",
        "weighted_discount_pct",
        "simple_discount_pct",
        "total_loss_dollars",
        "loss_item_share_pct",
        "loss_order_share_pct",
    ]
    for key in expected_keys:
        assert key in scorecard
