"""Data cleaning and feature engineering module for Retail Intelligence.

Transforms the raw Superstore dataset into a high-quality, standardized,
analysis-ready tabular dataset.
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from src.config import (
        COLUMN_MAPPING,
        DATASET_ENCODING,
        DISCOUNT_BINS,
        DISCOUNT_LABELS,
        PROCESSED_DATA_DIR,
        PROCESSED_DATA_FILE,
        RAW_DATA_FILE,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.config import (
        COLUMN_MAPPING,
        DATASET_ENCODING,
        DISCOUNT_BINS,
        DISCOUNT_LABELS,
        PROCESSED_DATA_DIR,
        PROCESSED_DATA_FILE,
        RAW_DATA_FILE,
    )


def standardize_postal_code(series: pd.Series) -> pd.Series:
    """Standardize US 5-digit postal codes.

    Handles float conversions (e.g. 42420.0 -> '42420'), pads with leading zeros,
    and cleanly preserves missing values (e.g. Burlington, VT known missing values).
    """
    def _clean_zip(val):
        if pd.isna(val) or val == "" or str(val).lower() == "nan":
            return np.nan
        # If float like 42420.0
        val_str = str(val).split(".")[0].strip()
        if val_str.isdigit():
            return val_str.zfill(5)
        return val_str

    return series.apply(_clean_zip)


def clean_retail_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich raw retail transactions.

    Args:
        df_raw: Raw DataFrame loaded directly from CSV.

    Returns:
        Cleaned, type-casted, and feature-engineered DataFrame.
    """
    # 1. Rename columns to standardized snake_case
    df = df_raw.rename(columns=COLUMN_MAPPING).copy()

    # 2. Trim string columns of whitespace
    str_cols = df.select_dtypes(include=["object", "str"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # 3. Parse Dates
    # Standard format in raw Superstore is M/D/YYYY or MM/DD/YYYY
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")

    # 4. Standardize Postal Code
    if "postal_code" in df.columns:
        df["postal_code"] = standardize_postal_code(df["postal_code"])

    # 5. Type casting for numerical variables
    df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce").astype("Int64")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").round(4)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").round(4)
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce").round(4)

    # 6. Feature Engineering
    # Shipping duration in calendar days
    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days

    # Time-based dimensions for trend analysis
    df["order_year"] = df["order_date"].dt.year
    df["order_quarter"] = df["order_date"].dt.to_period("Q").astype(str)
    df["order_year_month"] = df["order_date"].dt.strftime("%Y-%m")

    # Discount segmentation bands
    df["discount_band"] = pd.cut(
        df["discount"],
        bins=DISCOUNT_BINS,
        labels=DISCOUNT_LABELS,
        include_lowest=True,
    )

    # Profitability classification flags
    df["is_profitable"] = df["profit"] >= 0
    df["is_loss"] = df["profit"] < 0

    # Line-item unit price and unit cost estimation
    # Sales = Quantity * Unit_Price * (1 - Discount) => Unit_Price = Sales / (Quantity * (1 - Discount))
    # Safe division: when discount is 1.0 (100%), price calculation avoids division by zero
    non_discounted_qty = df["quantity"] * (1.0 - df["discount"])
    df["unit_price"] = np.where(
        non_discounted_qty > 0,
        (df["sales"] / non_discounted_qty).round(4),
        np.nan,
    )

    # Line-item profit margin (Note: for line-level categorization only.
    # Group-level profit margin must always be sum(profit) / sum(sales))
    df["line_profit_margin"] = np.where(
        df["sales"] > 0,
        (df["profit"] / df["sales"]).round(4),
        0.0,
    )

    return df


def process_dataset(
    input_path: Path = RAW_DATA_FILE,
    output_path: Path = PROCESSED_DATA_FILE,
) -> pd.DataFrame:
    """Load raw dataset, clean it, and save the processed version to disk.

    Args:
        input_path: Path to raw CSV file.
        output_path: Destination path for cleaned CSV.

    Returns:
        Cleaned pandas DataFrame.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {input_path}. Please run download script first."
        )

    print(f"[INFO] Reading raw dataset from: {input_path}")
    df_raw = pd.read_csv(input_path, encoding=DATASET_ENCODING)

    print(f"[INFO] Cleaning and feature engineering {len(df_raw):,} records...")
    df_clean = clean_retail_data(df_raw)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    print(f"[SUCCESS] Cleaned dataset written to: {output_path}")
    print(f"          Processed shape: {df_clean.shape[0]:,} rows x {df_clean.shape[1]} columns")

    return df_clean


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean retail dataset and output processed data")
    parser.add_argument("--input", type=Path, default=RAW_DATA_FILE, help="Path to raw CSV")
    parser.add_argument("--output", type=Path, default=PROCESSED_DATA_FILE, help="Path to output CSV")
    args = parser.parse_args()

    process_dataset(input_path=args.input, output_path=args.output)
