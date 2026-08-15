from flask import Flask, render_template, request, jsonify
import uuid
import json
import os
import traceback

from helpers.sales import insert_sale, fetch_filtered_records, get_record_by_rowid, delete_record, update_record, invoice, fetch_record_by_rowid
from helpers.loans import insert_loan
from helpers.inventory import add_to_inventory, get_categorized_inventory, update_inventory, delete_inventory
from helpers.sales_analytics import fetch_months, fetch_analytics_by_month
from helpers.suggestions import get_address_suggestions, get_address_suggestions_editable, fetch_inventory_suggestions, get_suggestions_with_id, delete_record_from_db, add_suggestion_to_db

import SessionVariables

app = Flask(__name__)

# =======================================================================================================================================
# SERVER STARTUP RENDERING
@app.route("/")
def index():
    gold_18c, gold_22c, silver = fetch_inventory_suggestions()
    address_suggestions, lowercase = get_address_suggestions_editable()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)
        
    return render_template("loans/loans.html", gold_18c_suggestions=gold_18c, gold_22c_suggestions=gold_22c, silver_suggestions=silver, address_suggestions=address_suggestions, lowercase=lowercase, admin_pass=config.get("admin_pass"))

#@app.route("/")
#def index():
#    gold_18c, gold_22c, silver = fetch_inventory_suggestions()
#    address_suggestions, lowercase = get_address_suggestions_editable()
#    config_path = os.path.join(os.path.dirname(__file__), "config.json")
#    with open(config_path) as f:
#        config = json.load(f)
#        
#    return render_template("sales/index.html", gold_18c_suggestions=gold_18c, gold_22c_suggestions=gold_22c, silver_suggestions=silver, address_suggestions=address_suggestions, lowercase=lowercase, admin_pass=config.get("admin_pass"), goldData=read_gold_data())

# APP NAVIGATION CHAIN
# ---- Sales 
@app.route("/sales/index.html")
def newsales_sales():
    gold_18c, gold_22c, silver = fetch_inventory_suggestions()
    address_suggestions, lowercase = get_address_suggestions_editable()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)
        
    return render_template("sales/index.html", gold_18c_suggestions=gold_18c, gold_22c_suggestions=gold_22c, silver_suggestions=silver, address_suggestions=address_suggestions, lowercase=lowercase, admin_pass=config.get("admin_pass"), goldData=read_gold_data())

@app.route("/sales/search-update.html")
def searchandupdate_sales():
    address_suggestions = get_address_suggestions()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    return render_template("sales/search-update.html", address_suggestions=address_suggestions, admin_pass=config.get("admin_pass"))

@app.route("/sales/invoice.html")
def bill():
    rowid = request.args.get("rowid", default=None, type=int)
    status = rowid is not None
    data, shopping, darabItems, log_payment = invoice(rowid)

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)
    return render_template("sales/invoice.html", data=data, shopping=shopping, darabItems=darabItems, log_payment=log_payment, status=status, storeName=config.get("store_name"), ownerName=config.get("owner_name"), storeAddress=config.get("store_address"), storeContact=config.get("store_contact"))

# ---- Inventory
@app.route("/inventory/inventory.html")
def test():
    inventory_18c, inventory_22c, inventory_silver, validation = get_categorized_inventory()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)

    return render_template("inventory/inventory.html", inventory_18c=inventory_18c, inventory_22c=inventory_22c, inventory_silver=inventory_silver, validation=validation, admin_pass=config.get("admin_pass"))

# ---- Admin
@app.route("/admin/sales-analytics.html")
def salesAnalytics():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)

    return render_template("/admin/sales-analytics.html", admin_pass=config.get("admin_pass"))

@app.route("/admin/change-presets.html")
def change_presets():
    address_suggestions, lowercase = get_suggestions_with_id()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)

    return render_template("/admin/change-presets.html", address_suggestions=address_suggestions, lowercase=lowercase, admin_pass=config.get("admin_pass"))

# =======================================================================================================================================
# BHAO RENDER AND UPDATE 
def read_gold_data():
    with open('gold.json', 'r') as file:
        return json.load(file)

def write_gold_data(data):
    with open('gold.json', 'w') as file:
        json.dump(data, file, indent=4)

@app.route('/gold-data', methods=['GET'])
def get_gold_data():
    return jsonify(read_gold_data())

@app.route('/update-gold-data', methods=['POST'])
def update_gold_data():
    new_data = request.get_json()
    write_gold_data(new_data)
    return jsonify({"status": "success", "message": "Gold data updated!"})

# =======================================================================================================================================
# ENTIRE SALES MANAGEMENT
# ---- ADD SALES RECORD
@app.route("/save_sales_record", methods=["POST"])
def save_record():
    try:
        data = request.json
        required_fields = ["date", "customer_name", "address", "phone_number", "purchase_details", "total_amount", "paid_amount", "credit", "remaining_credit", "bhao"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        if insert_sale(data):
            return jsonify({"message": "Record saved successfully"}), 200
        else:
            return jsonify({"error": "Database insertion failed"}), 500

    except Exception as e:
        traceback.print_exc()  
        return jsonify({"error": str(e)}), 500

# ---- FILTER SALES BASED ON ROWID [ returns partial data ]
@app.route('/sales_search_by_rowid', methods=['POST'])
def sales_search_by_rowid():
    SessionVariables.current_sale_search_active_id = "CANCELLED"

    data = request.get_json()
    rowid = data.get('rowid')
    if not rowid:
        return jsonify({"error": "No rowid provided"}), 400
    result_dict = fetch_record_by_rowid(rowid)
    if not result_dict:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(result_dict)

# ---- Cancle search session based on user events like refresh , page change !!
@app.route("/cancel_search", methods=["POST"])
def cancel_search():
    SessionVariables.current_sale_search_active_id = "CANCELLED"
    print("🛑 [SERVER] Active search cancelled.")
    return jsonify({"status": "cancelled"})

@app.route("/search_sales", methods=["POST"])
def search_records():
    search_id = str(uuid.uuid4())
    SessionVariables.current_sale_search_active_id = search_id

    data = request.json
    filters = data.get("filters", {})
    last_record_id = data.get("last_record_id", None)
    order = data.get("order", "ASC") 
    max_results = int(data.get("max_results", 50))

    response_data = fetch_filtered_records(filters, last_record_id, order, search_id, max_results)
    return jsonify(response_data) if response_data else ("", 204)

@app.route("/load_more_sales", methods=["POST"])
def fetch_more_records():
    search_id = str(uuid.uuid4())
    SessionVariables.current_sale_search_active_id = search_id

    data = request.json
    filters = data.get("filters", {})
    last_record_id = data.get("last_record_id", None)
    order = data.get("order", "ASC")
    max_results = int(data.get("max_results", 50))

    response_data = fetch_filtered_records(filters, last_record_id, order, search_id, max_results)
    return jsonify(response_data) if response_data else ("", 204)

# ---- FETCH SPECIFIC RECORD [ returns complete data ]
@app.route("/get-record_sales/<int:rowid>", methods=["GET"])
def get_record(rowid):
    """API endpoint to fetch a sales record by row ID."""
    record = get_record_by_rowid(rowid)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    return jsonify(record)

# ---- DELETE SPECIFIC RECORD 
@app.route("/delete-sales-record/<int:rowid>", methods=["DELETE"])
def remove_record(rowid):
    """Delete a record if found."""
    if delete_record(rowid):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Deletion failed"}), 400

# ---- UPDATE SPECIFIC RECORD
@app.route("/update-sales-record", methods=["POST"])
def modify_record():
    """Update a record with provided data."""
    data = request.json
    if update_record(data):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Update failed"}), 400

# ==================================================================================================================================
# LOAN MANAGEMENT

# ---- New Loan
@app.route("/save_loans_record", methods=["POST"])
def save_loan_record():
    try:
        data = request.json
        required_fields = ["date", "customer_name", "address", "phone_number", "item_details", "total_amount", "intrest", "paymentDetails"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        if insert_loan(data):
            return jsonify({"message": "Record saved successfully"}), 200
        else:
            return jsonify({"error": "Database insertion failed"}), 500

    except Exception as e:
        traceback.print_exc()  
        return jsonify({"error": str(e)}), 500
# ==================================================================================================================================
# INVENTORY MANAGEMENT 

# ---- ADDING NEW ITEM TO INVENTORY 
@app.route("/add-inventory", methods=["POST"])
def add_inventory():
    data = request.json
    name = data.get("name")
    quantity = data.get("quantity")
    weight = data.get("weight")
    weight_threshold = data.get("weight_threshold", 0)
    quantity_threshold = data.get("quantity_threshold", 0)

    if not name or quantity is None or weight is None:
        return jsonify(success=False, message="Missing data")

    result = add_to_inventory(name, quantity, weight, weight_threshold, quantity_threshold)
    
    if result["success"]:
        return jsonify(success=True, rowid=result["rowid"])
    else:
        return jsonify(success=False, message=result.get("error", "DB error"))

@app.route("/update-inventory", methods=["POST"])
def update_inventory_route():
    data = request.json
    success = update_inventory(data["id"], data["weight"], data["quantity"], data["threshold_weight"], data["threshold_quantity"])
    return jsonify({"success": success})

@app.route("/delete-inventory", methods=["POST"])
def delete_inventory_route():
    data = request.json
    success = delete_inventory(data["id"])
    return jsonify({"success": success})

# ==================================================================================================================================
# ADMIN MANAGEMENT 

# ---- SALES ANALYTICS MANAGEMENT 
@app.route('/get_months_analytics', methods=['GET'])
def get_months():
    months = fetch_months()
    return jsonify(months)

@app.route('/get_analytics', methods=['GET'])
def get_analytics():
    month = request.args.get('month')
    if not month:
        return jsonify({'error': 'Month is required'}), 400

    row = fetch_analytics_by_month(month)
    if row:
        return jsonify({
            'month': row['month'],
            'total_sales': row['total_sales'],
            'total_credit': row['total_credit'],
            'sold_items': json.loads(row['sold_items'])
        })
    return jsonify({'error': 'No data found'}), 404
    
# ---- Change Presets Management
@app.route("/delete-suggestion", methods=["POST"])
def delete_suggestion():
    """Handles deletion request from the frontend."""
    data = request.get_json()
    rowid = data.get("rowid")

    if not rowid:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    success = delete_record_from_db(rowid)
    if success:
        return jsonify({"success": True, "message": "Record deleted"}), 200
    else:
        return jsonify({"success": False, "message": "Failed to delete record"}), 500

@app.route("/add-suggestion", methods=["POST"])
def add_suggestion():
    """Handles adding a new suggestion from the frontend."""
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    rowid = add_suggestion_to_db(name)
    if rowid:
        return jsonify({"success": True, "message": "Record added", "rowid": rowid}), 200
    else:
        return jsonify({"success": False, "message": "Failed to add record"}), 500

# ==================================================================================================================================

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)