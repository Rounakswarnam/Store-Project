import sqlite3

def delete_sales_records_sequentially(database_path):
    try:
        # Connect to the SQLite database
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()

            # Start a transaction to ensure all deletions happen at once
            cursor.execute("BEGIN TRANSACTION")

            # Fetch all the row IDs from the sales table (use 'rowid')
            cursor.execute("SELECT rowid FROM sales_analytics")
            records = cursor.fetchall()

            # Delete each record sequentially
            for record in records:
                row_id = record[0]  # Get the row ID
                cursor.execute("DELETE FROM sales WHERE rowid = ?", (row_id,))
                print(f"Deleted record with rowid: {row_id}")

            # Commit the transaction to save all deletions
            conn.commit()
            print("All records have been deleted successfully!")

    except sqlite3.Error as e:
        # Handle database errors
        print(f"Database Error: {e}")
        return False

    return True

if __name__ == "__main__":

    # Call the function to delete the sales records
    delete_sales_records_sequentially("database.db")
