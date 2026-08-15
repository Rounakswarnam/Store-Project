import sqlite3

def export_schema(db_path, output_path="schema.sql"):
    with sqlite3.connect(db_path) as conn:
        with open(output_path, "w") as f:
            for line in conn.iterdump():
                if line.startswith("CREATE TABLE") or line.startswith("CREATE INDEX") or line.startswith("PRAGMA"):
                    f.write(f"{line}\n")

#export_schema("database.db")

def initialize_database_from_schema(new_db_path, schema_path="schema.sql"):
    with sqlite3.connect(new_db_path) as conn:
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
    print("✅ Database initialized from schema!")

initialize_database_from_schema("database.db")
