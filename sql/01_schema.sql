-- ============================================================================
-- Retail Intelligence Database Schema
-- Table: retail_orders
-- Description: Clean transactional store data with analytical features
-- ============================================================================

DROP TABLE IF EXISTS retail_orders;

CREATE TABLE retail_orders (
    row_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    ship_date TEXT NOT NULL,
    ship_mode TEXT,
    customer_id TEXT NOT NULL,
    customer_name TEXT,
    segment TEXT,
    country TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    region TEXT,
    product_id TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    product_name TEXT,
    sales REAL NOT NULL CHECK(sales >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    discount REAL NOT NULL CHECK(discount >= 0.0 AND discount <= 1.0),
    profit REAL NOT NULL,
    shipping_days INTEGER,
    order_year INTEGER,
    order_quarter TEXT,
    order_year_month TEXT,
    discount_band TEXT,
    is_profitable INTEGER NOT NULL CHECK(is_profitable IN (0, 1)),
    is_loss INTEGER NOT NULL CHECK(is_loss IN (0, 1)),
    unit_price REAL,
    line_profit_margin REAL
);

-- Indexes supporting critical analytical workloads
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON retail_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON retail_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON retail_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_category_subcategory ON retail_orders(category, sub_category);
CREATE INDEX IF NOT EXISTS idx_orders_region_state ON retail_orders(region, state);
CREATE INDEX IF NOT EXISTS idx_orders_discount_band ON retail_orders(discount_band);
CREATE INDEX IF NOT EXISTS idx_orders_profit ON retail_orders(profit);
