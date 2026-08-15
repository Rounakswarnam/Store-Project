import random
import json
from datetime import datetime, timedelta
import sqlite3

# Config
TOTAL_RECORDS = 100_000 
BATCH_SIZE = 10_000

NAMES = ["Rounak Swarnam", "Amit Sharma", "Priya Singh", "Sunita Yadav", "Rajesh Kumar"]
ADDRESSES = ["Test Address", "Patna, Bihar", "Delhi", "Mumbai", "Kolkata"]
PHONES = ["7717742611", "9801234567", "9123456789", "7890123456", "7001234567"]

ITEM_TYPES = [
    {"type": "Gold 18C", "article": "Dholna"},
    {"type": "Gold 22C", "article": "Jitiya"},
    {"type": "Silver", "article": "Bracelet"},
    {"type": "General Gold", "article": "Maangalsutra"},
    {"type": "General Silver", "article": "Bhichiya"},
]

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_items():
    items = []
    for _ in range(random.randint(1, 5)):
        choice = random.choice(ITEM_TYPES)
        weight = random.randint(5, 50)
        price = random.randint(50, 500)
        items.append({
            "type": choice["type"],
            "article": choice["article"],
            "weight": weight,
            "price": price
        })
    return items

def generate_payment_details(start_date, principal, rate, num_payments=3):
    payments = []
    current_principal = principal
    last_date = start_date
    for _ in range(num_payments):
        pay_date = last_date + timedelta(days=random.randint(20, 60))
        intrest_deduction = round(current_principal * (rate / 100), 2)
        payment_amount = intrest_deduction + random.randint(10, 50)

        remaining_post_intrest = max(payment_amount - intrest_deduction, 0)
        updated_principal = max(current_principal - remaining_post_intrest, 0)
        updated_monthly_intrest = round(updated_principal * (rate / 100), 2)

        payments.append({
            "payment_date": pay_date.strftime("%Y-%m-%d"),
            "payment_amount": payment_amount,
            "current_principal": current_principal,
            "intrest_date_slot": f"{last_date.strftime('%Y-%m-%d')} - {pay_date.strftime('%Y-%m-%d')}",
            "intrest_deduction": intrest_deduction,
            "remaining_post_intrest": remaining_post_intrest,
            "updated_principal": updated_principal,
            "updated_monthly_intrest": updated_monthly_intrest
        })

        current_principal = updated_principal
        last_date = pay_date

        if current_principal <= 0:
            break
    return payments

def main():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        date TEXT,
        customer_name TEXT,
        address TEXT,
        phone_number TEXT,
        item_details TEXT,
        total_amount REAL,
        intrest REAL,
        paymentDetails TEXT
    )
    """)

    insert_sql = """INSERT INTO loans 
        (date, customer_name, address, phone_number, item_details, total_amount, intrest, paymentDetails)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 12, 31)

    batch = []
    for i in range(1, TOTAL_RECORDS + 1):
        date = random_date(start_date, end_date)
        name = random.choice(NAMES)
        address = random.choice(ADDRESSES)
        phone = random.choice(PHONES)

        items = generate_items()
        total_amount = sum([it["price"] for it in items])
        intrest = random.randint(3, 12)  

        payments = generate_payment_details(date, total_amount, intrest, num_payments=random.randint(1, 5))

        row = (
            date.strftime("%Y-%m-%d"),
            name,
            address,
            phone,
            json.dumps(items),
            total_amount,
            intrest,
            json.dumps(payments)
        )
        batch.append(row)

        if i % BATCH_SIZE == 0:
            cur.execute("BEGIN")
            cur.executemany(insert_sql, batch)
            conn.commit()
            batch.clear()
            print(f"Inserted {i} records...")

    if batch:
        cur.execute("BEGIN")
        cur.executemany(insert_sql, batch)
        conn.commit()

    conn.close()
    print("Done inserting loans data.")

if __name__ == "__main__":
    main()
