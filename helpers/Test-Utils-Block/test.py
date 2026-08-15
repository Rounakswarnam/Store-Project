import sqlite3
import json

def main():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM loans LIMIT 100")
    rows = cur.fetchall()

    for idx, row in enumerate(rows, start=1):
        # handle extra id or any added column safely
        date = row[0]
        customer_name = row[1]
        address = row[2]
        phone = row[3]
        item_details = row[4]
        total = row[5]
        intrest = row[6]
        paymentDetails = row[7]

        print(f"\n--- Record {idx} ---")
        print(f"Date: {date}")
        print(f"Customer: {customer_name}")
        print(f"Address: {address}")
        print(f"Phone: {phone}")
        print(f"Total Amount: {total}")
        print(f"Interest Rate: {intrest}%")

        print("Items:")
        for item in json.loads(item_details):
            print(f"  - {item}")

        print("Payments:")
        for pay in json.loads(paymentDetails):
            print(f"  - {pay}")

    conn.close()

if __name__ == "__main__":
    main()
