"""Core analytical metrics and KPI calculations.

Defines industry-standard retail performance measures with defensive handling
for zero-sales scenarios and clear separation of order-level vs line-item aggregations.
"""

from typing import Any, Dict
import pandas as pd


def total_sales(df: pd.DataFrame) -> float:
    """Calculate total net sales revenue."""
    if "sales" not in df.columns or df.empty:
        return 0.0
    return float(df["sales"].sum())


def total_profit(df: pd.DataFrame) -> float:
    """Calculate total net profit (positive or negative)."""
    if "profit" not in df.columns or df.empty:
        return 0.0
    return float(df["profit"].sum())


def overall_profit_margin(df: pd.DataFrame) -> float:
    """Calculate overall profit margin percentage: (sum(profit) / sum(sales)) * 100.

    CRITICAL NOTE:
        Never calculate overall margin by taking the arithmetic mean of individual
        line-item margins (e.g. df['line_profit_margin'].mean()), as that treats a
        $5 item and a $5,000 order equally. Always aggregate numerator and denominator
        first before dividing.
    """
    sales = total_sales(df)
    if sales == 0.0:
        return 0.0
    profit = total_profit(df)
    return round((profit / sales) * 100.0, 4)


def total_distinct_orders(df: pd.DataFrame) -> int:
    """Calculate count of unique orders (avoiding double-counting line items)."""
    if "order_id" not in df.columns or df.empty:
        return 0
    return int(df["order_id"].nunique())


def total_distinct_customers(df: pd.DataFrame) -> int:
    """Calculate count of unique customers."""
    if "customer_id" not in df.columns or df.empty:
        return 0
    return int(df["customer_id"].nunique())


def total_units_sold(df: pd.DataFrame) -> int:
    """Calculate total physical units sold."""
    if "quantity" not in df.columns or df.empty:
        return 0
    return int(df["quantity"].sum())


def average_order_value(df: pd.DataFrame) -> float:
    """Calculate Average Order Value (AOV): total sales / distinct orders."""
    orders = total_distinct_orders(df)
    if orders == 0:
        return 0.0
    return round(total_sales(df) / orders, 2)


def net_sales_weighted_discount_proxy(df: pd.DataFrame) -> float:
    """Calculate net-sales-weighted discount proxy rate.

    Formula: sum(sales * discount) / sum(sales)
    IMPORTANT SEMANTIC NOTE:
        In this dataset, 'sales' represents net post-discount transaction revenue.
        Therefore, weighting by 'sales' weights discounts by net revenue rather than
        original list price. Because items with steep discounts generate proportionally
        lower net sales, this metric acts as a net-revenue-weighted discount proxy (14.04%),
        rather than the gross list price concession rate.
    """
    sales = total_sales(df)
    if sales == 0.0 or "discount" not in df.columns:
        return 0.0
    weighted_sum = float((df["sales"] * df["discount"]).sum())
    return round((weighted_sum / sales) * 100.0, 4)


# Alias for backward compatibility
sales_weighted_discount = net_sales_weighted_discount_proxy


def gross_list_sales(df: pd.DataFrame) -> float:
    """Estimate gross pre-discount list sales.

    Formula: sum(sales / (1 - discount)) where discount < 1.0.
    """
    if "sales" not in df.columns or "discount" not in df.columns or df.empty:
        return 0.0
    valid_mask = df["discount"] < 1.0
    gross = (df.loc[valid_mask, "sales"] / (1.0 - df.loc[valid_mask, "discount"])).sum()
    return round(float(gross), 2)


def gross_discount_rate(df: pd.DataFrame) -> float:
    """Calculate the true economic discount concession relative to gross list sales.

    Formula: (Gross List Sales - Net Sales) / Gross List Sales * 100
    Reflects the actual percentage of gross list value forfeited to discounts (~19.79%).
    """
    gross = gross_list_sales(df)
    net = total_sales(df)
    if gross <= 0.0:
        return 0.0
    concession = max(gross - net, 0.0)
    return round((concession / gross) * 100.0, 4)


def simple_average_discount(df: pd.DataFrame) -> float:
    """Calculate arithmetic mean of discount column across all line items (15.62%)."""
    if "discount" not in df.columns or df.empty:
        return 0.0
    return round(float(df["discount"].mean()) * 100.0, 4)


def loss_analysis_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate loss-making transactions and their revenue/profit impact."""
    if df.empty or "profit" not in df.columns:
        return {
            "loss_line_items": 0,
            "loss_item_share_pct": 0.0,
            "total_loss_dollars": 0.0,
            "loss_orders_count": 0,
            "loss_order_share_pct": 0.0,
        }

    loss_mask = df["profit"] < 0
    loss_items = df[loss_mask]
    total_orders = total_distinct_orders(df)

    loss_orders_cnt = int(loss_items["order_id"].nunique()) if "order_id" in loss_items.columns else 0
    loss_items_cnt = len(loss_items)

    return {
        "loss_line_items": loss_items_cnt,
        "loss_item_share_pct": round((loss_items_cnt / len(df)) * 100.0, 2) if len(df) > 0 else 0.0,
        "total_loss_dollars": round(float(loss_items["profit"].sum()), 2),
        "loss_orders_count": loss_orders_cnt,
        "loss_order_share_pct": round((loss_orders_cnt / total_orders) * 100.0, 2) if total_orders > 0 else 0.0,
    }


def executive_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate consolidated executive KPI scorecard."""
    loss_summary = loss_analysis_summary(df)
    return {
        "total_sales": round(total_sales(df), 2),
        "total_profit": round(total_profit(df), 2),
        "profit_margin_pct": round(overall_profit_margin(df), 2),
        "total_orders": total_distinct_orders(df),
        "total_customers": total_distinct_customers(df),
        "total_units": total_units_sold(df),
        "average_order_value": average_order_value(df),
        "weighted_discount_pct": round(sales_weighted_discount(df), 2),
        "simple_discount_pct": round(simple_average_discount(df), 2),
        "total_loss_dollars": loss_summary["total_loss_dollars"],
        "loss_item_share_pct": loss_summary["loss_item_share_pct"],
        "loss_order_share_pct": loss_summary["loss_order_share_pct"],
    }
