"""Database manager for the Retail Intelligence analytics project.

Initializes the local SQLite analytical database, executes schema migrations,
loads cleaned retail transactions, and provides query execution utilities.
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Union
import pandas as pd

try:
    from src.config import DATABASE_PATH, PROCESSED_DATA_FILE, SQL_DIR
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.config import DATABASE_PATH, PROCESSED_DATA_FILE, SQL_DIR

SCHEMA_FILE = SQL_DIR / "01_schema.sql"


def get_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Create and return a configured connection to the SQLite database.

    Enables foreign keys and sets row_factory to sqlite3.Row for dict-like access.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(
    schema_path: Path = SCHEMA_FILE,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Execute DDL script to create tables and indexes.

    Args:
        schema_path: Path to the .sql schema file.
        db_path: Path to the target SQLite database file.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)

    print(f"[SUCCESS] Database schema initialized from: {schema_path.name}")


def load_cleaned_data_to_db(
    csv_path: Path = PROCESSED_DATA_FILE,
    db_path: Path = DATABASE_PATH,
) -> int:
    """Load cleaned transaction data into the SQLite retail_orders table.

    Args:
        csv_path: Path to the processed CSV file.
        db_path: Path to the SQLite database file.

    Returns:
        Number of records successfully loaded into the database.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed data file not found at: {csv_path}. Run cleaning pipeline first."
        )

    df = pd.read_csv(csv_path)

    # Convert booleans to SQLite integers (1 / 0)
    for bool_col in ["is_profitable", "is_loss"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].astype(int)

    # Fill NA postal codes with empty string to preserve SQLite text constraints cleanly
    if "postal_code" in df.columns:
        df["postal_code"] = df["postal_code"].fillna("")

    # Align columns to database schema
    expected_cols = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "customer_name", "segment", "country", "city",
        "state", "postal_code", "region", "product_id", "category",
        "sub_category", "product_name", "sales", "quantity", "discount",
        "profit", "shipping_days", "order_year", "order_quarter",
        "order_year_month", "discount_band", "is_profitable", "is_loss",
        "unit_price", "line_profit_margin",
    ]
    df_to_load = df[[c for c in expected_cols if c in df.columns]]

    with get_connection(db_path) as conn:
        # Check current row count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM retail_orders;")
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute("DELETE FROM retail_orders;")

        df_to_load.to_sql(
            name="retail_orders",
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        cursor.execute("SELECT COUNT(*) FROM retail_orders;")
        loaded_count = cursor.fetchone()[0]

    print(f"[SUCCESS] Loaded {loaded_count:,} records into 'retail_orders' table in {db_path.name}")
    return loaded_count


def execute_sql_query(
    query_or_path: Union[str, Path],
    db_path: Path = DATABASE_PATH,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """Execute an analytical SQL query and return results as a pandas DataFrame.

    Args:
        query_or_path: Raw SQL query string or Path to a .sql file.
        db_path: Path to the target SQLite database.
        params: Optional query parameters.

    Returns:
        DataFrame containing query results.
    """
    if isinstance(query_or_path, Path) or (
        isinstance(query_or_path, str) and query_or_path.endswith(".sql")
    ):
        sql_file = Path(query_or_path)
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL file not found at: {sql_file}")
        with open(sql_file, "r", encoding="utf-8") as f:
            query = f.read()
    else:
        query = query_or_path

    with get_connection(db_path) as conn:
        df_result = pd.read_sql_query(query, conn, params=params)

    return df_result


def build_database(
    db_path: Path = DATABASE_PATH,
    schema_path: Path = SCHEMA_FILE,
    csv_path: Path = PROCESSED_DATA_FILE,
) -> None:
    """Orchestrate schema migration and data loading."""
    init_schema(schema_path=schema_path, db_path=db_path)
    load_cleaned_data_to_db(csv_path=csv_path, db_path=db_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize and populate Retail SQLite Database")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild schema and reload data")
    args = parser.parse_args()

    build_database()
