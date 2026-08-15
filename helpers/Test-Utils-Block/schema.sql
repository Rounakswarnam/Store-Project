CREATE TABLE address_presets (
            address TEXT NOT NULL UNIQUE
        );
CREATE TABLE inventory (
    article_name TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    weight REAL NOT NULL CHECK(weight >= 0)
, weight_threshold REAL DEFAULT 0, quantity_threshold INTEGER DEFAULT 0);
CREATE TABLE sales (
                date TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                shopping_details TEXT NOT NULL,  -- Stores JSON string
                darab TEXT,
                total_amount REAL NOT NULL,
                paid_amount REAL NOT NULL,
                credit INTEGER NOT NULL,
                remaining_credit REAL NOT NULL,
                credit_payment_history TEXT DEFAULT NULL
            , bhao TEXT);
CREATE TABLE sales_analytics (
                month TEXT PRIMARY KEY,  -- Unique month-year key
                total_sales REAL NOT NULL,
                total_credit REAL NOT NULL,
                sold_items TEXT NOT NULL  -- JSON storing aggregated item data
            );
