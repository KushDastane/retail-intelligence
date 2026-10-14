"""Data validation module for Retail Intelligence.

Performs rigorous structural, logical, and domain-level integrity checks
to ensure all analytical findings and downstream reports are built on clean data.
"""

import sys
from typing import Any, Dict, List, Optional
import pandas as pd

try:
    from src.config import MANDATORY_COLUMNS
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.config import MANDATORY_COLUMNS


class ValidationError(Exception):
    """Custom exception raised when retail data fails integrity checks."""
    pass


def validate_required_columns(
    df: pd.DataFrame,
    required_cols: Optional[List[str]] = None,
) -> None:
    """Validate that all required columns are present in the DataFrame.

    Raises:
        ValidationError: If any required column is missing.
    """
    if required_cols is None:
        required_cols = MANDATORY_COLUMNS

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValidationError(
            f"Schema validation failed. Missing {len(missing)} required columns: {missing}"
        )


def validate_missing_values(
    df: pd.DataFrame,
    critical_cols: Optional[List[str]] = None,
) -> Dict[str, int]:
    """Ensure critical business fields have zero null / NaN values.

    Raises:
        ValidationError: If null values exist in any critical column.
    """
    if critical_cols is None:
        critical_cols = MANDATORY_COLUMNS

    null_counts = {}
    failing_cols = {}
    for col in critical_cols:
        if col in df.columns:
            count = int(df[col].isna().sum())
            null_counts[col] = count
            if count > 0:
                failing_cols[col] = count

    if failing_cols:
        raise ValidationError(
            f"Critical columns contain unexpected null values: {failing_cols}"
        )

    return null_counts


def validate_date_logic(df: pd.DataFrame) -> None:
    """Validate temporal consistency between order and shipping dates.

    Checks:
    1. Neither order_date nor ship_date contain nulls.
    2. Shipping date is never earlier than order date (ship_date >= order_date).
    3. Order dates fall within a reasonable retail historical range.

    Raises:
        ValidationError: If temporal anomalies are detected.
    """
    if "order_date" not in df.columns or "ship_date" not in df.columns:
        raise ValidationError("Cannot validate date logic: 'order_date' or 'ship_date' missing.")

    if df["order_date"].isna().any():
        raise ValidationError("Found null values in 'order_date'.")

    if df["ship_date"].isna().any():
        raise ValidationError("Found null values in 'ship_date'.")

    # Business rule: an item cannot ship before it is ordered
    invalid_shipping = df[df["ship_date"] < df["order_date"]]
    if not invalid_shipping.empty:
        sample_ids = invalid_shipping["order_id"].head(5).tolist()
        raise ValidationError(
            f"Temporal violation: {len(invalid_shipping)} line items have ship_date < order_date. "
            f"Sample order IDs: {sample_ids}"
        )

    # Plausible date window check
    min_year = df["order_date"].dt.year.min()
    max_year = df["order_date"].dt.year.max()
    if min_year < 2000 or max_year > 2035:
        raise ValidationError(
            f"Plausibility check failed: Order date year range ({min_year} to {max_year}) is anomalous."
        )


def validate_numeric_domains(df: pd.DataFrame) -> None:
    """Validate that numeric fields adhere to retail domain rules.

    Checks:
    1. Sales must be non-negative (sales >= 0).
    2. Quantity must be strictly positive (quantity >= 1).
    3. Discount must be between 0.0 (0%) and 1.0 (100%).

    Raises:
        ValidationError: If values fall outside their valid retail domains.
    """
    if "sales" in df.columns:
        neg_sales = df[df["sales"] < 0]
        if not neg_sales.empty:
            raise ValidationError(
                f"Domain violation: {len(neg_sales)} records have negative sales."
            )

    if "quantity" in df.columns:
        invalid_qty = df[df["quantity"] <= 0]
        if not invalid_qty.empty:
            raise ValidationError(
                f"Domain violation: {len(invalid_qty)} records have quantity <= 0."
            )

    if "discount" in df.columns:
        invalid_discount = df[(df["discount"] < 0.0) | (df["discount"] > 1.0)]
        if not invalid_discount.empty:
            raise ValidationError(
                f"Domain violation: {len(invalid_discount)} records have discount outside [0.0, 1.0]."
            )


def validate_uniqueness(df: pd.DataFrame) -> None:
    """Validate primary key uniqueness.

    Checks:
    1. 'row_id' must be unique across all rows.

    Raises:
        ValidationError: If duplicate row IDs are found.
    """
    if "row_id" in df.columns:
        duplicates = df[df["row_id"].duplicated(keep=False)]
        if not duplicates.empty:
            raise ValidationError(
                f"Primary key uniqueness failed: Found {len(duplicates)} records with duplicate row_id."
            )


def run_validation_suite(df: pd.DataFrame) -> Dict[str, Any]:
    """Execute all validation checks and return a diagnostic report.

    Args:
        df: Cleaned or raw DataFrame.

    Returns:
        Dictionary summarizing validation results, record counts, and date spans.

    Raises:
        ValidationError: If any critical validation check fails.
    """
    validate_required_columns(df)
    null_report = validate_missing_values(df)
    validate_date_logic(df)
    validate_numeric_domains(df)
    validate_uniqueness(df)

    report = {
        "status": "PASSED",
        "total_records": len(df),
        "distinct_orders": int(df["order_id"].nunique()) if "order_id" in df.columns else None,
        "distinct_customers": int(df["customer_id"].nunique()) if "customer_id" in df.columns else None,
        "min_order_date": str(df["order_date"].min()) if "order_date" in df.columns else None,
        "max_order_date": str(df["order_date"].max()) if "order_date" in df.columns else None,
        "null_counts": null_report,
    }
    return report
