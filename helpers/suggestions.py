import sqlite3

# RENDER SUGGESTIONS WITH ROWID [ADMIN]
def get_suggestions_with_id():
    """Fetch suggestions with rowid, and a list of all addresses in lowercase."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, address FROM address_presets")
    rows = cursor.fetchall()

    results = [{"id": row[0], "name": row[1]} for row in rows]
    lowercase_addresses = [row[1].lower() for row in rows]

    conn.close()
    return results, lowercase_addresses

# DELETE A SUGGESTION [ADMIN]
def delete_record_from_db(rowid):
    """Deletes a record from the given table using rowid."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM address_presets WHERE rowid = ?", (rowid,))
    conn.commit()
    conn.close()
    return True

# ADD A NEW SUGGESTION [ADMIN]
def add_suggestion_to_db(name):
    """Adds a new suggestion to the given table and returns the new rowid."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO address_presets (address) VALUES (?)", (name,))
    conn.commit()
    rowid = cursor.lastrowid  
    conn.close()
    return rowid

# RANDER SUGGESTIONS IN DIFFERENT PAGES 
def get_address_suggestions_editable():
    """Fetch suggestions from the given table where column matches the query."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT address FROM address_presets")
    rows = cursor.fetchall()
    results = [row[0] for row in rows]
    lowercase_addresses = [row[0].lower() for row in rows]
    conn.close()
    return results, lowercase_addresses

def get_address_suggestions():
    """Fetch suggestions from the given table where column matches the query."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT address FROM address_presets")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def fetch_inventory_suggestions():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    def get_items(carat_filter=None):
        items = []
        if carat_filter:
            query = "SELECT article_name, quantity, weight, quantity_threshold, weight_threshold FROM inventory WHERE article_name LIKE ?"
            param = f"%_Gold {carat_filter}" 
        else:
            query = "SELECT article_name, quantity, weight, quantity_threshold, weight_threshold FROM inventory WHERE article_name LIKE ?"
            param = "%_Silver"

        cursor.execute(query, (param,))
        for name, qty, wt, t_qty, t_wt in cursor.fetchall():
            if carat_filter:
                suffix = f"_Gold {carat_filter}"
            else:
                suffix = "_Silver"
            if name.endswith(suffix):
                base_name = name[: -len(suffix)]
            else:
                base_name = name  

            if qty == 0 or wt == 0:
                status = "unavailable"
            elif qty <= t_qty or wt <= t_wt:
                status = "vulnerable"
            else:
                status = "available"

            items.append({"name": base_name, "status": status})
        return items

    gold_18c_suggestions = get_items("18C")
    gold_22c_suggestions = get_items("22C")
    silver_suggestions = get_items(None)

    conn.close()

    return gold_18c_suggestions, gold_22c_suggestions, silver_suggestions


# ENSURE THAT ALL ADDRESSES EXIST
def ensure_address_exists(address):
    """Checks if the address exists in the address_presets table (case-insensitive).
    If not, adds it to the table."""
    if not address:
        return

    address_clean = address.strip().lower()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT LOWER(address) FROM address_presets")
    existing = [row[0] for row in cursor.fetchall()]

    if address_clean not in existing:
        try:
            cursor.execute("INSERT INTO address_presets (address) VALUES (?)", (address.strip(),))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # already exists due to UNIQUE constraint
    conn.close()
