import sqlite3
import json

from helpers.sales_analytics import update_analytics_on_insert, update_analytics_on_update, update_analytics_on_delete
from helpers.inventory import shrink_inventory_after_sale
from helpers.suggestions import ensure_address_exists

import SessionVariables

DATABASE = "database.db"

# CREATE TABLE
def create_database():
    """Creates the sales table if it does not exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
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
            );
        """)
        conn.commit()

# ADDING RECORD 
def insert_sale(data):
    """Inserts sales record into the database."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            shopping_details_json = json.dumps(data["purchase_details"])
            darab_json = json.dumps(data["darab"])
            bhao_json = json.dumps(data["bhao"])

            credit_payment_history = None
            if int(data["credit"]) == 1 and data["remaining_credit"] > 0:
                credit_payment_history = json.dumps([
                    {
                        "date": data["date"],
                        "paid": data["paid_amount"],
                        "remaining_credit": data["remaining_credit"]
                    }
                ])

            cursor.execute("""
                INSERT INTO sales (date, customer_name, address, phone_number, shopping_details, darab, total_amount, paid_amount, credit, remaining_credit, credit_payment_history, bhao) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["date"],
                data["customer_name"],
                data["address"],
                data["phone_number"],
                shopping_details_json,
                darab_json,
                data["total_amount"],
                data["paid_amount"],
                int(data["credit"]), 
                data["remaining_credit"],
                credit_payment_history,
                bhao_json
            ))

            conn.commit()

            shrink_inventory_after_sale(data["purchase_details"])
            update_analytics_on_insert(data)
            ensure_address_exists(data["address"])
            
            return True
    except Exception as e:
        print("Database Error:", e)
        return False


# QUERYING DB IN CHUNKS OF 50
def fetch_filtered_records(filters, last_record_id=None, order="ASC", search_id=None, max_results=50):
    print(f"🔍 [START] Optimized chunked index-based fetch (limit={max_results})...")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    rowid_chunksize = 1000 if order.upper() == "DESC" else 100000

    #max_results = 50
    is_desc = order.upper() == "DESC"

    cursor.execute("SELECT MAX(rowid) FROM sales")
    max_rowid = cursor.fetchone()[0] or 0
    current_rowid = last_record_id or (max_rowid if is_desc else 0)

    intersect_queries = []
    no_filter_mode = False

    def inline_like(field, value):
        return f"{field} LIKE '{value.replace('%','').replace('_','')}%'"

    # 🧪 Detect empty filters
    if not filters:
        no_filter_mode = True

    if "phone_number" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE {inline_like('phone_number', filters['phone_number'])}")
    if "customer_name" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE {inline_like('customer_name', filters['customer_name'])}")
    if "address" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE {inline_like('address', filters['address'])}")
    if "date" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE date = '{filters['date']}'")
    elif "date_after" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE date > '{filters['date_after']}'")
    elif "date_before" in filters:
        intersect_queries.append(f"SELECT rowid FROM sales WHERE date < '{filters['date_before']}'")
    elif "date_range" in filters:
        lower, upper = filters["date_range"]
        if lower and upper and lower > upper:
            return {"error": "Invalid date range"}
        intersect_queries.append(f"SELECT rowid FROM sales WHERE date BETWEEN '{lower}' AND '{upper}'")

    if "credit" in filters:
        clause = f"credit = {int(filters['credit'])}"
        if "lower_credit" in filters and "upper_credit" in filters:
            clause += f" AND remaining_credit BETWEEN {filters['lower_credit']} AND {filters['upper_credit']}"
        elif "lower_credit" in filters:
            clause += f" AND remaining_credit >= {filters['lower_credit']}"
        elif "upper_credit" in filters:
            clause += f" AND remaining_credit <= {filters['upper_credit']}"
        elif "exact_credit" in filters:
            clause += f" AND remaining_credit = {filters['exact_credit']}"
        intersect_queries.append(f"SELECT rowid FROM sales WHERE {clause}")

    found_rowids = []
    has_more = False

    while True:
        #from app import active_search_id  # Import from root Flask file
        if search_id != SessionVariables.current_sale_search_active_id:
            print("🚫 [CANCEL] Search ID mismatch — aborting search.")
            conn.close()
            return

        if is_desc:
            range_start = max(0, current_rowid - rowid_chunksize)
            range_end = current_rowid
        else:
            range_start = current_rowid + 1
            range_end = current_rowid + rowid_chunksize

        rowid_condition = f"rowid BETWEEN {range_start} AND {range_end}"
        print(f"📦 [BATCH] RowIDs: {range_start} to {range_end}")

        if no_filter_mode:
            base_query = f"""
                SELECT rowid FROM sales 
                WHERE {rowid_condition}
                ORDER BY rowid {order}
            """
            cursor.execute(base_query)
        else:
            ranged_queries = [
                q.replace("WHERE", f"WHERE {rowid_condition} AND", 1)
                for q in intersect_queries
            ]
            final_query = f" INTERSECT ".join(ranged_queries) + f" ORDER BY rowid {order}"
            cursor.execute(final_query)

        rows = [r[0] for r in cursor.fetchall()]
        print(f"🔎 [MATCH] Found {len(rows)} rowids")

        for rid in rows:
            if rid not in found_rowids:
                found_rowids.append(rid)
            if len(found_rowids) > max_results:
                has_more = True
                break

        if len(found_rowids) >= max_results + 1:
            found_rowids = found_rowids[:max_results]
            break

        if len(rows) == 0:
            if (not is_desc and range_start > max_rowid) or (is_desc and range_end <= 0):
                break
            else:
                current_rowid = range_start if is_desc else range_end
                continue

        current_rowid = range_start if is_desc else range_end

    if not found_rowids:
        print("🚫 [EXIT] No matches.")
        return {"records": [], "has_more": False}

    #from app import active_search_id  # Import from root Flask file
    if search_id != SessionVariables.current_sale_search_active_id:
        print("🚫 [CANCEL] Aborted before final fetch.")
        conn.close()
        return

    found_rowids = found_rowids[:max_results + 1]
    placeholders = ",".join("?" for _ in found_rowids)
    full_query = f'''
        SELECT rowid, date, customer_name, address, phone_number,
               total_amount, paid_amount, credit, remaining_credit
        FROM sales WHERE rowid IN ({placeholders})
        ORDER BY rowid {order}
    '''
    cursor.execute(full_query, found_rowids)
    rows = cursor.fetchall()

    results = []
    for row in rows[:max_results]:
        results.append({
            "id": row[0],
            "date": row[1],
            "customer_name": row[2],
            "address": row[3],
            "phone_number": row[4],
            "total_amount": row[5],
            "paid_amount": row[6],
            "remaining_credit": row[8]
        })

    print(f"✅ [DONE] {len(results)} records returned.")
    print("🔁 [HAS MORE]:", has_more)

    conn.close()

    return {
        "records": results,
        "has_more": has_more
    }

# QUERYING THE DATABSE BASED ON ROWID 
def fetch_record_by_rowid(rowid):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, * FROM sales WHERE rowid = ?", (rowid,))
    record = cursor.fetchone()
    conn.close()

    if not record:
        return None

    return {
        "id": record[0],
        "date": record[1],
        "customer_name": record[2],
        "address": record[3],
        "phone_number": record[4],
        "total_amount": record[7],
        "paid_amount": record[8],
        "remaining_credit": record[10]
    }

# FETCHING FULL DATA OF SPECIF RECORD
def get_record_by_rowid(rowid):
    """Fetch a record from the database using rowid."""
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        cursor.execute("SELECT rowid, * FROM sales WHERE rowid = ?", (rowid,))
        record = cursor.fetchone()

        if not record:
            return None 

        shopping_details = json.loads(record["shopping_details"])
        darab = json.loads(record["darab"])
        bhao = json.loads(record["bhao"])
        credit_payment_history = []
        if record["credit_payment_history"]:
            try:
                credit_payment_history = json.loads(record["credit_payment_history"])
            except json.JSONDecodeError:
                pass  

        return {
            "rowid": record["rowid"],
            "date": record["date"],
            "customer_name": record["customer_name"],
            "address": record["address"],
            "phone_number": record["phone_number"],
            "shopping_details": shopping_details,
            "total_amount": record["total_amount"],
            "paid_amount": record["paid_amount"],
            "credit": record["credit"],
            "remaining_credit": record["remaining_credit"],
            "credit_payment_history": credit_payment_history,
            "darab": darab,
            "bhao": bhao
        }

# DELETE A SPECIFIC RECORD 
def delete_record(rowid):
    """Delete a sales record and update analytics accordingly."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT date, remaining_credit, total_amount, shopping_details FROM sales WHERE rowid = ?", (rowid,))
        sale_record = cursor.fetchone()

        if not sale_record:
            print(f"Sale record with rowid {rowid} not found.")
            return False

        sale_date, remaining_credit, total_amount, shopping_details_json = sale_record
        month = sale_date[:7]  

        shopping_details = json.loads(shopping_details_json) 

        update_analytics_on_delete(month, total_amount, remaining_credit, shopping_details)

        cursor.execute("DELETE FROM sales WHERE rowid = ?", (rowid,))
        conn.commit()
        return cursor.rowcount > 0

# UPDATE A SPECIFIC RECORD
def update_record(data):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT date, paid_amount, remaining_credit, credit, credit_payment_history FROM sales WHERE rowid = ?", (data["rowid"],))
        old_record = cursor.fetchone()

        if not old_record:
            print(f"Sale record with rowid {data['rowid']} not found.")
            return False

        sale_date, old_paid, old_remaining_credit, old_credit, old_history_json = old_record
        month = sale_date[:7]

        new_entry = None
        log_payment = (
            old_credit == 1 and  
            (data["paid_amount"] != old_paid or data["remaining_credit"] != old_remaining_credit)
        )

        if log_payment:
            new_entry = {
                "date": data["date"],
                "paid": data["paid_amount"] - old_paid,
                "remaining_credit": data["remaining_credit"]
            }

        if new_entry:
            if old_history_json:
                history = json.loads(old_history_json)
            else:
                history = []
            history.append(new_entry)
            updated_history = json.dumps(history)
        else:
            updated_history = old_history_json

        cursor.execute("""
            UPDATE sales
            SET customer_name = ?, address = ?, phone_number = ?, 
                paid_amount = ?, remaining_credit = ?, credit = ?, 
                credit_payment_history = ?
            WHERE rowid = ?
        """, (
            data["customer_name"],
            data["address"],
            data["phone_number"],
            data["paid_amount"],
            data["remaining_credit"],
            data["credit"],
            updated_history,
            data["rowid"]
        ))

        conn.commit()
        update_analytics_on_update(month, old_remaining_credit, data["remaining_credit"])
        return cursor.rowcount > 0

# NEW SALES INVOCE 
def invoice(rowid=None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if rowid is not None:
        cursor.execute("""SELECT rowid, * FROM sales WHERE rowid = ?""", (rowid,))
    else:
        cursor.execute("""SELECT rowid, * FROM sales ORDER BY rowid DESC LIMIT 1""")

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None, None  

    data = {
        "rowid": row[0],
        "date": row[1],
        "name": row[2],
        "address": row[3],
        "phone": row[4],
        "total": row[7],
        "paid": row[8],
        "remaining": row[10]
    }

    try:
        items = json.loads(row[5])
    except json.JSONDecodeError:
        items = []
    shopping = []
    for item in items:
        material_type = item.get("type", "")
        type_label = ""

        if material_type == "Gold 18C":
            type_label = "18C (750 HM)"
        elif material_type == "Gold 22C":
            type_label = "22C (916 HM)"
        elif material_type == "Silver":
            type_label = "Silver"
        else:
            type_label = "Unknown"

        shopping.append({
            "type": type_label,
            "name": item.get("article", ""),
            "rate": item.get("rate", ""),
            "make": item.get("makeing" ""),
            "weight": item.get("weight", ""),
            "price": item.get("price", "")
        })

    try:
        darabItems = json.loads(row[6])
    except json.JSONDecodeError:
        darabItems = []
    darab = []
    for item in darabItems:
        material_type = item.get("type", "")
        type_label = ""

        if material_type == "Gold 18C":
            type_label = "18C (750 HM)"
        elif material_type == "Gold 22C":
            type_label = "22C (916 HM)"
        elif material_type == "Silver":
            type_label = "Silver"
        elif material_type == "General Gold":
            type_label = "Gen Gold"
        elif material_type == "General Silver":
            type_label = "Gen SIlver"
        else:
            type_label = "Unknown"

        darab.append({
            "type": type_label,
            "name": item.get("article", ""),
            "rate": item.get("rate", ""),
            "weight": item.get("weight", ""),
            "price": item.get("price", "")
        })

    try:
        log_payment_raw = row[11]
        if log_payment_raw is None:
            log_payment = []
        else:
            log_payment = json.loads(log_payment_raw)
    except (json.JSONDecodeError, TypeError):
        log_payment = []

    return data, shopping, darab, log_payment

