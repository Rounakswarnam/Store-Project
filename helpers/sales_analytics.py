import sqlite3
import json

DATABASE = "database.db"

# ANALYTICS TABLE SETUP

def create_analytics_table():
    """Creates the sales_analytics table with month as PRIMARY KEY."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS sales_analytics")
        cursor.execute("""
            CREATE TABLE sales_analytics (
                month TEXT PRIMARY KEY,  -- Unique month-year key
                total_sales REAL NOT NULL,
                total_credit REAL NOT NULL,
                sold_items TEXT NOT NULL  -- JSON storing aggregated item data
            );
        """)
        conn.commit()
        print("✅ sales_analytics table created successfully!")

# UPDATE ANALYTICS ON NEW SALE
def update_analytics_on_insert(data):
    """Updates analytics when a new sale is inserted."""
    month = data["date"][:7]  # Extract YYYY-MM
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT total_sales, total_credit, sold_items FROM sales_analytics WHERE month = ?", (month,))
        record = cursor.fetchone()

        if record:
            total_sales, total_credit, sold_items_json = record
            sold_items = json.loads(sold_items_json)
        else:
            total_sales, total_credit, sold_items = 0, 0, {}

        total_sales += float(data["total_amount"])  
        total_credit += float(data["remaining_credit"]) 

        for item in data["purchase_details"]:
            key = f"{item['article']}_{item['type']}"

            item_weight = float(item["weight"])
            item_price = float(item["price"])

            if key in sold_items:
                sold_items[key]["count"] += 1
                sold_items[key]["weight"] += item_weight
                sold_items[key]["price"] += item_price
            else:
                sold_items[key] = {
                    "count": 1,
                    "weight": item_weight,
                    "price": item_price
                }

        cursor.execute("""
            INSERT INTO sales_analytics (month, total_sales, total_credit, sold_items)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(month) DO UPDATE 
            SET total_sales = excluded.total_sales, 
                total_credit = excluded.total_credit,
                sold_items = excluded.sold_items
        """, (month, total_sales, total_credit, json.dumps(sold_items)))
        conn.commit()

# UPDATE ANALYTICS UPON SALES RECORD UPDATE
def update_analytics_on_update(month, old_remaining_credit, new_remaining_credit):
    """Update total_credit when a sale record is modified."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT total_credit FROM sales_analytics WHERE month = ?", (month,))
        analytics_record = cursor.fetchone()

        if not analytics_record:
            print(f"Analytics record for month {month} not found.")
            return False
        total_credit = analytics_record[0]

        new_total_credit = float(total_credit) - float(old_remaining_credit) + float(new_remaining_credit)

        cursor.execute("""
            UPDATE sales_analytics
            SET total_credit = ?
            WHERE month = ?
        """, (new_total_credit, month))
        conn.commit()
        return True

# UPDATE ANALYTICS UPON SALES RECORD DELETION
def update_analytics_on_delete(month, total_amount, remaining_credit, shopping_details):
    """Update analytics when a sale is deleted."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT total_sales, total_credit, sold_items FROM sales_analytics WHERE month = ?", (month,))
        record = cursor.fetchone()

        if not record:
            print(f"Analytics record for month {month} not found.")
            return False

        total_sales, total_credit, sold_items_json = record
        sold_items = json.loads(sold_items_json)

        total_sales -= float(total_amount)
        total_credit -= float(remaining_credit)

        for item in shopping_details:
            key = f"{item['article']}_{item['type']}"

            item_weight = float(item["weight"])
            item_price = float(item["price"])
            
            if key in sold_items:
                if sold_items[key]["count"] > 1:
                    sold_items[key]["count"] -= 1
                    sold_items[key]["weight"] -= item_weight
                    sold_items[key]["price"] -= item_price
                else:
                    del sold_items[key]  

        if total_sales > 0 or total_credit > 0:
            cursor.execute("""
                UPDATE sales_analytics
                SET total_sales = ?, total_credit = ?, sold_items = ?
                WHERE month = ?
            """, (total_sales, total_credit, json.dumps(sold_items), month))
        else:
            cursor.execute("DELETE FROM sales_analytics WHERE month = ?", (month,))  

        conn.commit()
        return True

# RENDER ANALYTICS 
def fetch_months():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT month FROM sales_analytics")
    months = [row['month'] for row in cursor.fetchall()]
    conn.close()
    return months

def fetch_analytics_by_month(month):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_analytics WHERE month = ?", (month,))
    row = cursor.fetchone()
    conn.close()
    return row
