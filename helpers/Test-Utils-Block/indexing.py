import sqlite3

def optimize_sales_table_indexes():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Step 1: Create indexes
    indexes = {
        "idx_customer_name": "CREATE INDEX IF NOT EXISTS idx_customer_name ON sales(customer_name)",
        "idx_phone_number": "CREATE INDEX IF NOT EXISTS idx_phone_number ON sales(phone_number)",
        "idx_address": "CREATE INDEX IF NOT EXISTS idx_address ON sales(address)",
        "idx_date": "CREATE INDEX IF NOT EXISTS idx_date ON sales(date)",
        "idx_credit": "CREATE INDEX IF NOT EXISTS idx_credit ON sales(credit)",
        "idx_remaining_credit": "CREATE INDEX IF NOT EXISTS idx_remaining_credit ON sales(remaining_credit)"
    }

    for name, ddl in indexes.items():
        cursor.execute(ddl)
        print(f"[✓] Ensured index: {name}")

    conn.commit()
    conn.close()

optimize_sales_table_indexes()