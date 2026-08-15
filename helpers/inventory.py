import sqlite3

# AUTOMETICALLY SHRINK INVENTORY ON SALES 
def shrink_inventory_after_sale(sale_items):
    try:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()

            for item in sale_items:
                article_name = item["article"].strip()
                weight_sold = float(item["weight"])
                type = item["type"]
                type_str = f"{article_name}_{type}"

                cursor.execute("SELECT rowid, quantity, weight FROM inventory WHERE LOWER(article_name) = LOWER(?)", (type_str,))
                record = cursor.fetchone()

                if not record:
                    print(f"[WARNING] Item not found in inventory: {type_str}")
                    continue

                rowid, quantity, weight = record

                new_quantity = max(quantity - 1, 0)
                new_weight = max(round(weight - weight_sold, 3), 0)

                # Update the inventory
                cursor.execute(
                    "UPDATE inventory SET quantity = ?, weight = ? WHERE rowid = ?",
                    (new_quantity, new_weight, rowid)
                )

            conn.commit()
        return True
    except Exception as e:
        print("[Inventory Shrink Error]:", e)
        return False

# ADD NEW RECORDS TO INVENTORY
def add_to_inventory(name, quantity, weight, weight_threshold, quantity_threshold):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO inventory (article_name, quantity, weight, weight_threshold, quantity_threshold) VALUES (?, ?, ?, ?, ?)""", (name, int(quantity), round(float(weight), 3), float(weight_threshold), int(quantity_threshold)))
        inserted_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "rowid": inserted_id}
    except Exception as e:
        print("[DB ERROR]", e)
        return {"success": False, "error": str(e)}

# RENDER INVENTORY PAGE
def get_categorized_inventory():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, article_name, quantity, weight, weight_threshold, quantity_threshold FROM inventory")
    records = cursor.fetchall()
    conn.close()

    inventory_18c = []
    inventory_22c = []
    inventory_silver = []
    validation = []

    for rowid, name, quantity, weight, weight_threshold, quantity_threshold in records:
        if "Gold 18C" in name:
            if quantity == 0 or weight == 0:
                status = "unavailable"
            elif quantity <= quantity_threshold or weight <= weight_threshold:
                status = "vulnerable"
            else:
                status = "available"
        
            stripped_name = name.replace("_Gold 18C", "")
            inventory_18c.append({"id": rowid, "type": "18C Gold", "name": stripped_name, "quantity": quantity, "weight": weight, "thresWeight": weight_threshold, "thresQuantity": quantity_threshold, "status": status})
        
        elif "Gold 22C" in name:
            if quantity == 0 or weight == 0:
                status = "unavailable"
            elif quantity <= quantity_threshold or weight <= weight_threshold:
                status = "vulnerable"
            else:
                status = "available"
        
            stripped_name = name.replace("_Gold 22C", "")
            inventory_22c.append({"id": rowid, "type": "22C Gold", "name": stripped_name, "quantity": quantity, "weight": weight, "thresWeight": weight_threshold, "thresQuantity": quantity_threshold, "status": status})
        
        elif "Silver" in name:
            if quantity == 0 or weight == 0:
                status = "unavailable"
            elif quantity <= quantity_threshold or weight <= weight_threshold:
                status = "vulnerable"
            else:
                status = "available"
        
            stripped_name = name.replace("_Silver", "")
            inventory_silver.append({"id": rowid, "type": "Silver", "name": stripped_name, "quantity": quantity, "weight": weight, "thresWeight": weight_threshold, "thresQuantity": quantity_threshold, "status": status})
        
        validation.append(name.lower())

    return inventory_18c, inventory_22c, inventory_silver, validation
    
# UPDATE INVENTORY
def update_inventory(rowid, weight, quantity, threshold_weight, threshold_quantity):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""UPDATE inventory SET weight = ?, quantity = ?, weight_threshold = ?, quantity_threshold = ? WHERE rowid = ?""", (weight, quantity, threshold_weight, threshold_quantity, rowid))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] Failed to update rowid {rowid}: {e}")
        return False

# DELETE INVENTORY
def delete_inventory(rowid):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE rowid = ?", (rowid,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] Failed to delete rowid {rowid}: {e}")
        return False