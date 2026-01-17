import glob
import os
import sqlite3

db_path = "data/app.diagnostic.db"
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

files = glob.glob("migrations/*_sqlite.sql")
files.sort()

for f in files:
    print(f"Executing {f}...")
    with open(f, "r") as sql_file:
        full_script = sql_file.read()
        # Split script by semicolon to execute one by one and find the error
        # Note: this is a simple split and might break some complex SQLs,
        # but for these migrations it should mostly work.
        statements = full_script.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"FAIL in {f} at statement:")
                print(stmt)
                print(f"ERROR: {e}")
                conn.close()
                exit(1)
        conn.commit()

conn.close()
print("All migrations completed successfully in diagnostic mode.")
