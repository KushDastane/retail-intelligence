"""Unit tests for retail data cleaning and validation logic."""

import numpy as np
import pandas as pd
import pytest

from src.data.clean import clean_retail_data, standardize_postal_code
from src.data.validate import (
    ValidationError,
    run_validation_suite,
    validate_date_logic,
    validate_missing_values,
    validate_numeric_domains,
    validate_required_columns,
    validate_uniqueness,
)


@pytest.fixture
def sample_valid_raw_df() -> pd.DataFrame:
    """Fixture providing a minimal, valid raw Superstore DataFrame."""
    return pd.DataFrame(
        {
            "Row ID": [1, 2, 3],
            "Order ID": ["CA-2016-152156", "CA-2016-152156", "CA-2016-138688"],
            "Order Date": ["11/8/2016", "11/8/2016", "6/12/2016"],
            "Ship Date": ["11/11/2016", "11/11/2016", "6/16/2016"],
            "Ship Mode": ["Second Class", "Second Class", "Second Class"],
            "Customer ID": ["CG-12520", "CG-12520", "DV-13045"],
            "Customer Name": ["Claire Gute", "Claire Gute", "Darrin Van Huff"],
            "Segment": ["Consumer", "Consumer", "Corporate"],
            "Country": ["United States", "United States", "United States"],
            "City": ["Henderson", "Henderson", "Los Angeles"],
            "State": ["Kentucky", "Kentucky", "California"],
            "Postal Code": [42420.0, 42420.0, 90036.0],
            "Region": ["South", "South", "West"],
            "Product ID": ["FUR-BO-10001798", "FUR-CH-10000454", "OFF-LA-10000240"],
            "Category": ["Furniture", "Furniture", "Office Supplies"],
            "Sub-Category": ["Bookcases", "Chairs", "Labels"],
            "Product Name": ["Bush Bookcase", "Hon Chair", "Self-Adhesive Labels"],
            "Sales": [261.96, 731.94, 14.62],
            "Quantity": [2, 3, 2],
            "Discount": [0.0, 0.0, 0.0],
            "Profit": [41.9136, 219.582, 6.8714],
        }
    )


def test_standardize_postal_code():
    """Verify postal code standardizer pads digits and handles missing values."""
    s = pd.Series([42420.0, "90036", 501, np.nan, ""])
    cleaned = standardize_postal_code(s)
    assert cleaned.iloc[0] == "42420"
    assert cleaned.iloc[1] == "90036"
    assert cleaned.iloc[2] == "00501"  # Zero-padded to 5 digits
    assert pd.isna(cleaned.iloc[3])
    assert pd.isna(cleaned.iloc[4])


def test_clean_retail_data(sample_valid_raw_df):
    """Verify that cleaning pipeline correctly renames columns, casts types, and adds features."""
    cleaned = clean_retail_data(sample_valid_raw_df)

    assert "order_id" in cleaned.columns
    assert "sales" in cleaned.columns
    assert "shipping_days" in cleaned.columns
    assert "discount_band" in cleaned.columns
    assert "is_profitable" in cleaned.columns
    assert "is_loss" in cleaned.columns

    # Verify shipping days: Nov 8 to Nov 11 = 3 days
    assert cleaned["shipping_days"].iloc[0] == 3
    # Verify discount band for 0.0 discount
    assert cleaned["discount_band"].iloc[0] == "0% (No Discount)"
    # Verify postal code standardized to string
    assert cleaned["postal_code"].iloc[0] == "42420"


def test_validation_suite_passes_on_valid_data(sample_valid_raw_df):
    """Verify that clean data passes the validation suite without errors."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    report = run_validation_suite(cleaned)

    assert report["status"] == "PASSED"
    assert report["total_records"] == 3
    assert report["distinct_orders"] == 2  # 2 rows share order CA-2016-152156


def test_missing_required_columns_raises():
    """Verify that missing required columns raise a ValidationError."""
    df_incomplete = pd.DataFrame({"order_id": ["O-1"], "sales": [100.0]})
    with pytest.raises(ValidationError, match="Missing.*required columns"):
        validate_required_columns(df_incomplete)


def test_null_in_critical_columns_raises(sample_valid_raw_df):
    """Verify that nulls in critical business columns trigger a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    cleaned.loc[0, "sales"] = np.nan

    with pytest.raises(ValidationError, match="Critical columns contain unexpected null values"):
        validate_missing_values(cleaned)


def test_ship_date_before_order_date_raises(sample_valid_raw_df):
    """Verify that a temporal violation (shipping before ordering) raises a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    # Set shipping date prior to order date
    cleaned.loc[0, "ship_date"] = pd.to_datetime("2016-11-01")
    cleaned.loc[0, "order_date"] = pd.to_datetime("2016-11-08")

    with pytest.raises(ValidationError, match="Temporal violation"):
        validate_date_logic(cleaned)


def test_negative_sales_raises(sample_valid_raw_df):
    """Verify that negative sales amount raises a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    cleaned.loc[0, "sales"] = -50.0

    with pytest.raises(ValidationError, match="Domain violation.*negative sales"):
        validate_numeric_domains(cleaned)


def test_zero_or_negative_quantity_raises(sample_valid_raw_df):
    """Verify that quantity <= 0 raises a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    cleaned.loc[0, "quantity"] = 0

    with pytest.raises(ValidationError, match="Domain violation.*quantity <= 0"):
        validate_numeric_domains(cleaned)


def test_discount_out_of_bounds_raises(sample_valid_raw_df):
    """Verify that discount > 1.0 or < 0.0 raises a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    cleaned.loc[0, "discount"] = 1.25

    with pytest.raises(ValidationError, match="Domain violation.*discount outside"):
        validate_numeric_domains(cleaned)


def test_duplicate_row_id_raises(sample_valid_raw_df):
    """Verify that duplicate row_id primary keys raise a ValidationError."""
    cleaned = clean_retail_data(sample_valid_raw_df)
    cleaned.loc[1, "row_id"] = cleaned.loc[0, "row_id"]

    with pytest.raises(ValidationError, match="Primary key uniqueness failed"):
        validate_uniqueness(cleaned)


def test_actual_processed_dataset_integrity():
    """Integration test: Verify the real processed dataset passes all validation rules."""
    from src.config import PROCESSED_DATA_FILE

    if not PROCESSED_DATA_FILE.exists():
        pytest.skip("Processed dataset not generated yet.")

    df = pd.read_csv(PROCESSED_DATA_FILE)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["ship_date"] = pd.to_datetime(df["ship_date"])

    report = run_validation_suite(df)
    assert report["status"] == "PASSED"
    assert report["total_records"] == 9994
    assert report["distinct_orders"] == 5009
    assert report["distinct_customers"] == 793

