import random
import json
from datetime import datetime, timedelta
import sqlite3

# --- Config ---
NAMES = [
    "Amit Sharma", "Rohit Verma", "Priya Singh", "Sunita Yadav", "Rajesh Kumar",
    "Sanjay Thakur", "Poonam Kumari", "Deepak Jha", "Kiran Devi", "Manish Sinha",
    "Neha Kumari", "Vinay Paswan", "Saurabh Mishra", "Rekha Devi", "Ravi Kishor"
]

PHONES = ["7717742611", "7766055777", "7717748339", "9999977777", "8888844444"]

# Real villages in Vaishali District, Bihar
VILLAGES = [
    "Mahua", "Desari", "Raghopur", "Bidupur", "Patepur", "Jandaha", "Goraul",
    "Hajipur", "Lalganj", "Sahdei Buzurg", "Chehrakala", "Bhagwanpur", "Mahnar",
    "Panchayat Bhawan", "Chandpura"
]

ARTICLES = ["Mangalsutra", "Jitiya", "Dholna", "Balla", "Chain", "Pauchi", "Bichua", "Nath"]
TYPES = ["Gold 18C", "Gold 22C", "Silver"]
BHAO = {"Gold 22C": 8800, "Gold 18C": 7500}
BATCH_SIZE = 100000

def random_date():
    base = datetime.today()
    delta = timedelta(days=random.randint(0, 365))
    return (base - delta).strftime("%Y-%m-%d")

def generate_shopping():
    items = []
    for _ in range(random.randint(1, 5)):
        typ = random.choice(TYPES)
        article = random.choice(ARTICLES)
        rate = random.randint(10, 100)
        makeing = random.randint(10, 50)
        weight = round(random.uniform(1, 20), 3)
        price = int(rate * weight + makeing)
        items.append({
            "type": typ,
            "article": article,
            "rate": rate,
            "makeing": makeing,
            "weight": round(weight, 3),
            "price": price
        })
    return items

def generate_darab():
    if random.choice([True, False]):
        return []
    items = []
    for _ in range(random.randint(1, 4)):
        typ = random.choice(["Gold 18C", "Gold 22C", "General Gold", "Silver", "General Silver"])
        article = random.choice(ARTICLES)
        rate = random.randint(40, 9000)
        weight = round(random.uniform(1, 30), 3)
        price = int(rate * weight)
        items.append({
            "type": typ,
            "article": article,
            "rate": rate,
            "weight": round(weight, 3),
            "price": price
        })
    return items

def generate_record():
    date = random_date()
    name = random.choice(NAMES)
    address = random.choice(VILLAGES)
    phone = random.choice(PHONES)
    shopping = generate_shopping()
    darab = generate_darab()
    total = int(sum(item["price"] for item in shopping))
    paid = int(random.uniform(0, total))
    credit = int(paid < total)
    remaining = total - paid if credit else 0

    credit_logs = [{
        "date": date,
        "paid": paid,
        "remaining_credit": remaining
    }] if credit and remaining > 0 else None

    return {
        "date": date,
        "customer_name": name,
        "address": address,
        "phone_number": phone,
        "purchase_details": shopping,
        "darab": darab,
        "total_amount": total,
        "paid_amount": paid,
        "credit": credit,
        "remaining_credit": remaining,
        "credit_payment_history": credit_logs, 
        "bhao": BHAO
    }

def batch_insert(conn, batch_data):
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO sales (date, customer_name, address, phone_number, shopping_details, darab, total_amount, paid_amount, credit, remaining_credit, credit_payment_history, bhao) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, batch_data)
    conn.commit()

if __name__ == "__main__":
    total_records = 50_000_000
    log_interval = 100_000

    print(total_records)
    
    conn = sqlite3.connect('database.db')  # Adjust if needed

    batch_data = []
    for i in range(1, total_records + 1):
        record = generate_record()
        shopping_details_json = json.dumps(record["purchase_details"])
        darab_json = json.dumps(record["darab"])
        bhao_json = json.dumps(record["bhao"])
        credit_payment_history = json.dumps(record["credit_payment_history"]) if record["credit"] else None
        
        batch_data.append((
            record["date"], 
            record["customer_name"], 
            record["address"], 
            record["phone_number"], 
            shopping_details_json, 
            darab_json, 
            record["total_amount"], 
            record["paid_amount"], 
            record["credit"], 
            record["remaining_credit"], 
            credit_payment_history, 
            bhao_json
        ))

        if i % BATCH_SIZE == 0:
            batch_insert(conn, batch_data)
            print(f"Inserted {i:,} records...")
            batch_data.clear()

    if batch_data:
        batch_insert(conn, batch_data)
        print(f"Inserted final {len(batch_data)} records...")

    conn.close()
