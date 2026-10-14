"""Unit tests for visualization data preparation and chart generation."""

from pathlib import Path
import pandas as pd
import pytest

from src.config import FIGURES_DIR, PROCESSED_DATA_FILE
from src.visualization import (
    prepare_customer_decile_data,
    prepare_discount_band_data,
    prepare_monthly_trend_data,
    prepare_regional_data,
    prepare_subcategory_data,
)


@pytest.fixture(scope="module")
def df_processed() -> pd.DataFrame:
    """Fixture providing clean DataFrame."""
    if not PROCESSED_DATA_FILE.exists():
        pytest.skip("Processed dataset not found.")
    return pd.read_csv(PROCESSED_DATA_FILE)


def test_prepare_monthly_trend_data(df_processed):
    """Verify monthly trend transformation produces 48 complete calendar months."""
    monthly = prepare_monthly_trend_data(df_processed)
    assert len(monthly) == 48
    assert "year_month" in monthly.columns
    assert "sales" in monthly.columns
    assert "profit" in monthly.columns
    assert "profit_margin_pct" in monthly.columns
    # Net sales sum matches total
    assert round(monthly["sales"].sum(), 2) == 2297200.86


def test_prepare_subcategory_data(df_processed):
    """Verify subcategory preparation returns all 17 subcategories and correctly flags loss leaders."""
    subcat = prepare_subcategory_data(df_processed)
    assert len(subcat) == 17
    # Lowest profit subcategory must be Tables
    assert subcat.iloc[0]["sub_category"] == "Tables"
    assert subcat.iloc[0]["profit"] < 0
    # Top profit subcategory must be Copiers
    assert subcat.iloc[-1]["sub_category"] == "Copiers"
    assert subcat.iloc[-1]["profit"] > 50000


def test_prepare_discount_band_data(df_processed):
    """Verify discount band preparation returns 6 bins totaling 9,994 items."""
    bands = prepare_discount_band_data(df_processed)
    assert len(bands) == 6
    assert bands["items"].sum() == 9994
    # Bands above 20% discount should have negative profit margins in this dataset
    deep_discount_band = bands[bands["discount_band"] == "> 50% (Deep Discount)"]
    assert not deep_discount_band.empty
    assert deep_discount_band["profit_margin_pct"].values[0] < -100.0


def test_prepare_regional_data(df_processed):
    """Verify regional aggregation covers 4 regions and identifies top loss states."""
    regional, loss_states = prepare_regional_data(df_processed)
    assert len(regional) == 4
    # West must be top profit region
    assert regional.iloc[0]["region"] == "West"
    # Texas must be top loss state
    assert loss_states.iloc[0]["state"] == "Texas"
    assert loss_states.iloc[0]["profit"] < -20000


def test_prepare_customer_decile_data(df_processed):
    """Verify customer deciles create 10 groups where Deciles 1-2 drive 80%+ profit."""
    deciles = prepare_customer_decile_data(df_processed)
    assert len(deciles) == 10
    assert deciles["customers"].sum() == 793
    # Top 2 deciles cumulative profit share >= 80%
    top_2_share = deciles.loc[deciles["decile"].isin([1, 2]), "profit"].sum() / deciles["profit"].sum()
    assert top_2_share > 0.80
    # Decile 10 has negative profit
    assert deciles.loc[deciles["decile"] == 10, "profit"].values[0] < 0


def test_generated_figures_exist_and_non_empty():
    """Verify all 5 publication-ready charts exist in reports/figures/ and are non-empty."""
    expected_files = [
        "01_monthly_sales_profit_trend.png",
        "02_category_subcategory_profitability.png",
        "03_discount_band_analysis.png",
        "04_regional_state_profitability.png",
        "05_customer_decile_pareto.png",
    ]
    for filename in expected_files:
        fig_path = FIGURES_DIR / filename
        assert fig_path.exists(), f"Figure {filename} was not generated."
        # Verify file size > 50 KB (ensuring valid, high-res rendered image)
        assert fig_path.stat().st_size > 50_000, f"Figure {filename} is suspiciously small."
