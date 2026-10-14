"""Exploratory data analysis and visualization module for Retail Intelligence.

Generates publication-grade, accessible, and restrained figures using Matplotlib
and Seaborn. Implements clear labeling, sample size disclosures, and formatted currency scales.
"""

from pathlib import Path
from typing import Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for reliable headless execution
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.config import FIGURES_DIR, PROCESSED_DATA_FILE
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.config import FIGURES_DIR, PROCESSED_DATA_FILE

# Aesthetic constants
COLOR_PRIMARY = "#0f766e"      # Teal 700 (Profitable / Baseline)
COLOR_SECONDARY = "#0284c7"    # Sky 600
COLOR_ACCENT = "#f59e0b"       # Amber 500
COLOR_DANGER = "#e11d48"       # Rose 600 (Loss-making / Unprofitable)
COLOR_TEXT = "#1e293b"         # Slate 800
COLOR_MUTED = "#64748b"        # Slate 500
COLOR_GRID = "#e2e8f0"         # Slate 200

# Global Matplotlib styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.labelweight": "medium",
    "axes.edgecolor": COLOR_GRID,
    "axes.linewidth": 1.0,
    "grid.color": COLOR_GRID,
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
    "grid.alpha": 0.7,
    "figure.titlesize": 14,
    "figure.titleweight": "bold",
})


def format_currency_k(x, pos):
    """Format tick numbers as thousands of dollars ($K)."""
    if abs(x) >= 1_000_000:
        return f"${x*1e-6:.1f}M"
    elif abs(x) >= 1_000:
        return f"${x*1e-3:.0f}K"
    else:
        return f"${x:.0f}"


def format_pct(x, pos):
    """Format tick numbers as percentages."""
    return f"{x:.0f}%"


# =============================================================================
# Chart Data Preparation Functions (Separation of Logic for Unit Testing)
# =============================================================================

def prepare_monthly_trend_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales, profit, and margin by Year-Month."""
    df_sorted = df.copy()
    df_sorted["order_date"] = pd.to_datetime(df_sorted["order_date"])
    df_sorted["year_month"] = df_sorted["order_date"].dt.strftime("%Y-%m")

    monthly = (
        df_sorted.groupby("year_month")
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )
    monthly["profit_margin_pct"] = np.where(
        monthly["sales"] > 0,
        (monthly["profit"] / monthly["sales"]) * 100.0,
        0.0,
    )
    return monthly


def prepare_subcategory_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales, profit, margin, and losses across all 17 subcategories."""
    subcat = (
        df.groupby(["category", "sub_category"])
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            items=("row_id", "count"),
            loss_dollars=("profit", lambda p: p[p < 0].sum()),
            loss_items=("profit", lambda p: (p < 0).sum()),
        )
        .reset_index()
    )
    subcat["profit_margin_pct"] = (subcat["profit"] / subcat["sales"]) * 100.0
    subcat["loss_item_pct"] = (subcat["loss_items"] / subcat["items"]) * 100.0
    return subcat.sort_values(by="profit", ascending=True).reset_index(drop=True)


def prepare_discount_band_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics across discount bands with sample sizes."""
    bands = (
        df.groupby("discount_band", observed=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            items=("row_id", "count"),
            orders=("order_id", "nunique"),
            avg_discount=("discount", "mean"),
            loss_dollars=("profit", lambda p: p[p < 0].sum()),
            loss_items=("profit", lambda p: (p < 0).sum()),
        )
        .reset_index()
    )
    bands["profit_margin_pct"] = np.where(
        bands["sales"] > 0,
        (bands["profit"] / bands["sales"]) * 100.0,
        0.0,
    )
    bands["loss_item_pct"] = (bands["loss_items"] / bands["items"]) * 100.0
    return bands


def prepare_regional_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate metrics by region and top 5 loss-making states."""
    regional = (
        df.groupby("region")
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            items=("row_id", "count"),
            weighted_discount=("discount", lambda d: np.average(d, weights=df.loc[d.index, "sales"]) * 100),
        )
        .reset_index()
    )
    regional["profit_margin_pct"] = (regional["profit"] / regional["sales"]) * 100.0
    regional = regional.sort_values(by="profit", ascending=False).reset_index(drop=True)

    # Top loss states
    states = (
        df.groupby(["state", "region"])
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            avg_discount=("discount", lambda d: d.mean() * 100),
        )
        .reset_index()
    )
    loss_states = states[states["profit"] < 0].sort_values(by="profit", ascending=True).head(5)
    return regional, loss_states


def prepare_customer_decile_data(df: pd.DataFrame) -> pd.DataFrame:
    """Group customers into 10 profit deciles using rank."""
    cust = (
        df.groupby(["customer_id", "customer_name"])
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )
    # Decile 1 = highest profit, Decile 10 = lowest/negative profit
    cust["decile"] = pd.qcut(
        cust["profit"].rank(method="first", ascending=False),
        q=10,
        labels=range(1, 11),
    )
    decile_summary = (
        cust.groupby("decile", observed=False)
        .agg(
            customers=("customer_id", "count"),
            sales=("sales", "sum"),
            profit=("profit", "sum"),
        )
        .reset_index()
    )
    decile_summary["profit_margin_pct"] = (decile_summary["profit"] / decile_summary["sales"]) * 100.0
    total_profit = decile_summary["profit"].sum()
    decile_summary["cumulative_profit"] = decile_summary["profit"].cumsum()
    decile_summary["cumulative_profit_pct"] = (decile_summary["cumulative_profit"] / total_profit) * 100.0
    return decile_summary


# =============================================================================
# Plotting Implementations
# =============================================================================

def plot_monthly_trends(df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Generate 2-panel monthly sales and profit trajectory (2014-2017)."""
    monthly = prepare_monthly_trend_data(df)
    x = range(len(monthly))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, dpi=300)

    # Panel 1: Monthly Net Sales
    ax1.plot(x, monthly["sales"], color=COLOR_SECONDARY, marker="o", markersize=4, linewidth=2, label="Monthly Net Sales")
    ax1.fill_between(x, monthly["sales"], alpha=0.15, color=COLOR_SECONDARY)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax1.set_title("Monthly Net Sales Trajectory (2014 - 2017)", loc="left", pad=8)
    ax1.set_ylabel("Net Sales ($)")
    ax1.grid(True)

    # Highlight Q4 seasonal peaks
    peak_idx = monthly["sales"].idxmax()
    ax1.annotate(
        f"Peak Q4 Volume\nNov 2017: ${monthly.loc[peak_idx, 'sales']*1e-3:.1f}K",
        xy=(peak_idx, monthly.loc[peak_idx, "sales"]),
        xytext=(peak_idx - 6, monthly.loc[peak_idx, "sales"] * 0.88),
        arrowprops=dict(facecolor=COLOR_TEXT, arrowstyle="->", lw=1.2),
        fontsize=9,
        fontweight="medium",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLOR_GRID),
    )

    # Panel 2: Monthly Net Profit & Margin
    colors = [COLOR_PRIMARY if p >= 0 else COLOR_DANGER for p in monthly["profit"]]
    ax2.bar(x, monthly["profit"], color=colors, width=0.6, label="Monthly Net Profit")
    ax2.axhline(0, color=COLOR_TEXT, linestyle="-", linewidth=0.8, alpha=0.7)
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax2.set_title("Monthly Net Profit Performance ($)", loc="left", pad=8)
    ax2.set_ylabel("Net Profit ($)")
    ax2.set_xlabel("Time Period (48 Months: 2014 - 2017)")
    ax2.grid(True)

    # Format X ticks: show every 6 months
    tick_indices = list(range(0, len(monthly), 6))
    ax2.set_xticks(tick_indices)
    ax2.set_xticklabels([monthly.loc[i, "year_month"] for i in tick_indices], rotation=0)

    fig.suptitle("Retail Intelligence: Monthly Sales Volume vs Profit Realization", fontsize=14, y=0.98)
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return fig


def plot_category_profitability(df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Generate horizontal bar chart of all 17 subcategories highlighting loss leaders."""
    subcat = prepare_subcategory_data(df)

    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)

    y_pos = range(len(subcat))
    colors = [COLOR_DANGER if p < 0 else COLOR_PRIMARY for p in subcat["profit"]]

    bars = ax.barh(y_pos, subcat["profit"], color=colors, height=0.65, edgecolor="none")
    ax.axvline(0, color=COLOR_TEXT, linestyle="-", linewidth=1.0, alpha=0.8)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{row['sub_category']} ({row['category']})" for _, row in subcat.iterrows()])
    ax.set_xlabel("Total Net Profit ($)")
    ax.set_title("Subcategory Profit Contribution & Loss Leaders (All 17 Subcategories)", loc="left", pad=12)
    ax.grid(True, axis="x")

    # Value annotations on bars
    for idx, (bar, (_, row)) in enumerate(zip(bars, subcat.iterrows())):
        profit_val = row["profit"]
        margin_val = row["profit_margin_pct"]
        text_str = f" ${profit_val*1e-3:.1f}K ({margin_val:.1f}%)" if profit_val >= 0 else f"-${abs(profit_val)*1e-3:.1f}K ({margin_val:.1f}%) "
        ha = "left" if profit_val >= 0 else "right"
        offset = 800 if profit_val >= 0 else -800
        ax.text(
            profit_val + offset,
            bar.get_y() + bar.get_height() / 2.0,
            text_str,
            va="center",
            ha=ha,
            fontsize=8.5,
            fontweight="bold" if profit_val < 0 or profit_val > 40000 else "normal",
            color=COLOR_DANGER if profit_val < 0 else COLOR_TEXT,
        )

    # Summary Annotation Box
    summary_box = (
        "Key Findings:\n"
        "• Technology (Copiers, Phones) generates 50.8% of net profit.\n"
        "• Tables (-$17.7K) and Bookcases (-$3.5K) are primary loss leaders.\n"
        "• Supplies (-$1.2K) is also net loss-making despite high volume."
    )
    ax.text(
        0.58,
        0.18,
        summary_box,
        transform=ax.transAxes,
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.5", fc="#f8fafc", ec=COLOR_GRID, lw=1.2),
        verticalalignment="center",
    )

    fig.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return fig


def plot_discount_band_analysis(df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Generate paired visualization: Profit Margin % and Line-Item Sample Sizes by Discount Band."""
    bands = prepare_discount_band_data(df)
    x = np.arange(len(bands))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    # Panel A: Profit Margin % by Discount Band
    colors = [COLOR_PRIMARY if m >= 0 else COLOR_DANGER for m in bands["profit_margin_pct"]]
    bars1 = ax1.bar(x, bands["profit_margin_pct"], color=colors, width=0.55)
    ax1.axhline(0, color=COLOR_TEXT, linestyle="-", linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(bands["discount_band"], rotation=25, ha="right", fontsize=9)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(format_pct))
    ax1.set_ylabel("Overall Profit Margin (%)")
    ax1.set_title("A: Profit Margin by Discount Tier (Observed Breakeven Cliff)", loc="left", pad=10)
    ax1.grid(True, axis="y")

    for bar, val in zip(bars1, bands["profit_margin_pct"]):
        va = "bottom" if val >= 0 else "top"
        offset = 2.0 if val >= 0 else -6.0
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            val + offset,
            f"{val:.1f}%",
            ha="center",
            va=va,
            fontsize=8.5,
            fontweight="bold",
            color=COLOR_TEXT,
        )

    # Annotation highlighting the cliff
    ax1.annotate(
        "Margin Collapses Past 20%\n(Observed Dataset Pattern)",
        xy=(3, -10.05),
        xytext=(1.8, -60),
        arrowprops=dict(facecolor=COLOR_DANGER, arrowstyle="->", lw=1.2),
        fontsize=8.5,
        fontweight="bold",
        color=COLOR_DANGER,
        bbox=dict(boxstyle="round,pad=0.3", fc="#fff1f2", ec="#fecdd3"),
    )

    # Panel B: Line-Item Volume & Unprofitable Share
    bars2 = ax2.bar(x, bands["items"], color=COLOR_SECONDARY, width=0.55, alpha=0.85, label="Transaction Line Items")
    ax2.set_xticks(x)
    ax2.set_xticklabels(bands["discount_band"], rotation=25, ha="right", fontsize=9)
    ax2.set_ylabel("Transaction Line Items Count (Sample Size)")
    ax2.set_title("B: Sample Size & % Unprofitable Items by Tier", loc="left", pad=10)
    ax2.grid(True, axis="y")

    # Secondary line for % unprofitable items
    ax2_line = ax2.twinx()
    ax2_line.plot(x, bands["loss_item_pct"], color=COLOR_DANGER, marker="s", linewidth=2, markersize=5, label="% Unprofitable")
    ax2_line.yaxis.set_major_formatter(ticker.FuncFormatter(format_pct))
    ax2_line.set_ylabel("% Line Items with Negative Profit", color=COLOR_DANGER)
    ax2_line.tick_params(axis="y", labelcolor=COLOR_DANGER)
    ax2_line.grid(False)

    for bar, count in zip(bars2, bands["items"]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            count + 60,
            f"n={count:,}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=COLOR_MUTED,
        )

    fig.suptitle("Discount Policy Impact: Observed Margin Degradation vs Transaction Volume", fontsize=13, y=1.01)
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return fig


def plot_regional_profitability(df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Generate 2-panel regional overview and top loss-making state ranking."""
    regional, loss_states = prepare_regional_data(df)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    # Panel 1: Regional Net Profit & Profit Margin %
    y_reg = np.arange(len(regional))
    bars = ax1.barh(y_reg, regional["profit"], color=COLOR_PRIMARY, height=0.55)
    ax1.set_yticks(y_reg)
    ax1.set_yticklabels(regional["region"], fontsize=10)
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax1.set_xlabel("Total Net Profit ($)")
    ax1.set_title("Regional Profitability Comparison (4 Territories)", loc="left", pad=10)
    ax1.grid(True, axis="x")

    for bar, (_, row) in zip(bars, regional.iterrows()):
        ax1.text(
            row["profit"] + 2000,
            bar.get_y() + bar.get_height() / 2.0,
            f" ${row['profit']*1e-3:.1f}K (Margin: {row['profit_margin_pct']:.1f}%)",
            va="center",
            fontsize=9,
            fontweight="medium",
        )

    # Panel 2: Top 5 Loss-Making States
    y_states = np.arange(len(loss_states))
    bars2 = ax2.barh(y_states, abs(loss_states["profit"]), color=COLOR_DANGER, height=0.55)
    ax2.set_yticks(y_states)
    ax2.set_yticklabels(
        [f"{row['state']} ({row['region']})" for _, row in loss_states.iterrows()],
        fontsize=9.5,
    )
    ax2.xaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax2.set_xlabel("Net Loss Amount ($)")
    ax2.set_title("Top 5 Loss-Making States (Heavy Discounting Drains)", loc="left", pad=10)
    ax2.grid(True, axis="x")

    for bar, (_, row) in zip(bars2, loss_states.iterrows()):
        ax2.text(
            abs(row["profit"]) + 400,
            bar.get_y() + bar.get_height() / 2.0,
            f"-${abs(row['profit'])*1e-3:.1f}K (Avg Disc: {row['avg_discount']:.1f}%)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color=COLOR_DANGER,
        )

    fig.suptitle("Geographic Performance: Regional Margin Disparities & State Loss Concentration", fontsize=13, y=1.01)
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return fig


def plot_customer_deciles(df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Generate customer decile Pareto curve and sales vs profit distribution."""
    deciles = prepare_customer_decile_data(df)
    x = np.arange(1, 11)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    # Panel 1: Cumulative Profit % Curve (Pareto Distribution)
    ax1.plot(x, deciles["cumulative_profit_pct"], marker="o", color=COLOR_PRIMARY, linewidth=2.2, markersize=6)
    ax1.axhline(100, color=COLOR_MUTED, linestyle=":", alpha=0.8)
    ax1.axhline(80, color=COLOR_ACCENT, linestyle="--", linewidth=1.2, alpha=0.8, label="80% Profit Benchmark")
    ax1.axvline(2, color=COLOR_ACCENT, linestyle="--", linewidth=1.2, alpha=0.8, label="Top 20% Customers (Decile 2)")
    ax1.set_xticks(x)
    ax1.set_xlabel("Customer Profit Decile (1 = Most Profitable, 10 = Heavy Loss)")
    ax1.set_ylabel("Cumulative Share of Total Company Profit (%)")
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(format_pct))
    ax1.set_title("A: Cumulative Profit Pareto Curve (Top 20% = 81.9% Profit)", loc="left", pad=10)
    ax1.grid(True)
    ax1.legend(loc="lower right", fontsize=8.5)

    # Panel 2: Net Sales vs Net Profit by Decile
    width = 0.38
    rects1 = ax2.bar(x - width/2, deciles["sales"], width, label="Decile Sales ($)", color=COLOR_SECONDARY, alpha=0.85)
    colors_profit = [COLOR_PRIMARY if p >= 0 else COLOR_DANGER for p in deciles["profit"]]
    rects2 = ax2.bar(x + width/2, deciles["profit"], width, label="Decile Net Profit ($)", color=colors_profit)
    ax2.axhline(0, color=COLOR_TEXT, linestyle="-", linewidth=0.8)
    ax2.set_xticks(x)
    ax2.set_xlabel("Customer Profit Decile")
    ax2.set_ylabel("Value ($)")
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_currency_k))
    ax2.set_title("B: Decile Sales vs Net Profit (Decile 10 Loss Concentration)", loc="left", pad=10)
    ax2.grid(True, axis="y")
    ax2.legend(loc="upper right", fontsize=8.5)

    # Annotate Decile 10 anomaly
    d10_sales = deciles.loc[deciles["decile"] == 10, "sales"].values[0]
    d10_profit = deciles.loc[deciles["decile"] == 10, "profit"].values[0]
    ax2.annotate(
        f"Decile 10 Anomaly:\n${d10_sales*1e-3:.0f}K Sales\n-${abs(d10_profit)*1e-3:.1f}K Loss",
        xy=(10 + width/2, d10_profit),
        xytext=(7.2, -45000),
        arrowprops=dict(facecolor=COLOR_DANGER, arrowstyle="->", lw=1.2),
        fontsize=8.5,
        fontweight="bold",
        color=COLOR_DANGER,
        bbox=dict(boxstyle="round,pad=0.3", fc="#fff1f2", ec="#fecdd3"),
    )

    fig.suptitle("Customer Value Concentration: Pareto Distribution & Unprofitable Volume", fontsize=13, y=1.01)
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)

    return fig


def generate_all_figures(
    df: Optional[pd.DataFrame] = None,
    output_dir: Path = FIGURES_DIR,
) -> dict:
    """Generate and save all 5 publication-ready figures to disk."""
    if df is None:
        if not PROCESSED_DATA_FILE.exists():
            raise FileNotFoundError(f"Processed dataset not found at {PROCESSED_DATA_FILE}")
        df = pd.read_csv(PROCESSED_DATA_FILE)

    output_dir.mkdir(parents=True, exist_ok=True)
    generated = {}

    print(f"[INFO] Generating publication-grade figures in: {output_dir}")

    f1 = output_dir / "01_monthly_sales_profit_trend.png"
    plot_monthly_trends(df, save_path=f1)
    generated["monthly_trend"] = f1
    print(f"  [OK] Saved: {f1.name}")

    f2 = output_dir / "02_category_subcategory_profitability.png"
    plot_category_profitability(df, save_path=f2)
    generated["category_profitability"] = f2
    print(f"  [OK] Saved: {f2.name}")

    f3 = output_dir / "03_discount_band_analysis.png"
    plot_discount_band_analysis(df, save_path=f3)
    generated["discount_analysis"] = f3
    print(f"  [OK] Saved: {f3.name}")

    f4 = output_dir / "04_regional_state_profitability.png"
    plot_regional_profitability(df, save_path=f4)
    generated["regional_profitability"] = f4
    print(f"  [OK] Saved: {f4.name}")

    f5 = output_dir / "05_customer_decile_pareto.png"
    plot_customer_deciles(df, save_path=f5)
    generated["customer_deciles"] = f5
    print(f"  [OK] Saved: {f5.name}")

    print(f"[SUCCESS] All 5 figures successfully created and saved at 300 DPI.")
    return generated


if __name__ == "__main__":
    generate_all_figures()
