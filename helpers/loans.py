import sqlite3
import json

#from helpers.suggestions import ensure_address_exists

DATABASE = "database.db"

def create_loans_table():
    # Connect to database (creates database.db if not exists)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create loans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            address TEXT,
            phone_number TEXT,
            item_details TEXT,
            total_amount REAL,
            intrest REAL,
            paymentDetails JSON
        )
    """)

    conn.commit()
    conn.close()
    print("✅ loans table created successfully!")

def insert_loan(data):
    """Inserts loans record into the database."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            item_details_json = json.dumps(data["item_details"])
            payment_details_json = json.dumps(data["paymentDetails"])

            cursor.execute("""
                INSERT INTO loans (
                    date,
                    customer_name,
                    address,
                    phone_number,
                    item_details,
                    total_amount,
                    intrest,
                    paymentDetails
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["date"],
                data["customer_name"],
                data["address"],
                data["phone_number"],
                item_details_json,
                data["total_amount"],
                data["intrest"],
                payment_details_json
            ))

            conn.commit()

            #update_analytics_on_insert(data)
            ensure_address_exists(data["address"])
            
            return True
    except Exception as e:
        print("Database Error:", e)
        return False