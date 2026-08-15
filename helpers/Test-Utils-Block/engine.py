import sqlite3

def fetch_filtered_records(filters, last_record_id=None, order="ASC"):
    print("🔍 [START] Optimized chunked index-based fetch...")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    rowid_chunksize = 1000 if order.upper() == "DESC" else 100000

    max_results = 50
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
        intersect_queries.append(f"SELECT rowid FROM sales WHERE {clause}")

    found_rowids = []
    has_more = False

    while True:
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




if __name__ == "__main__":
    filters = {
        "phone_number": "7717742611",
        "credit": 1,
        "lower_credit": 100,
        "upper_credit": 500,
        "date_range": ("2023-12-01", "2023-12-31"),
        "customer_name": "Amit",
        "address": "Des"
    }

    result = fetch_filtered_records(
        filters=filters,
        last_record_id=None,  # or pass a rowid for pagination
        order="ASC"
    )

    print("\n📦 Final Output:")
    for rec in result["records"]:
        print(rec)

    print("🔁 Has More:", result["has_more"])
