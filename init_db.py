import os
import sqlite3
import glob

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
db_path = "data/app.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted existing database.")

# Define missing SQLs
employees_sql = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code VARCHAR(10) UNIQUE NOT NULL,     -- E0001
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50),                        -- 机械部/电气部/PMC
    role VARCHAR(50),                              -- 机械工程师/调试工程师
    phone VARCHAR(20),
    wechat_userid VARCHAR(50),                     -- 企业微信UserID
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

payments_sql = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_type VARCHAR(20),  -- RECEIVE/PAY
    status VARCHAR(20) DEFAULT 'PENDING',
    payment_date DATE,
    payer_name VARCHAR(100),
    payee_name VARCHAR(100),
    bank_account VARCHAR(100),
    transaction_no VARCHAR(100),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Write missing migration files
with open("migrations/00000001_initial_employees_sqlite.sql", "w") as f:
    f.write(employees_sql)

with open("migrations/00000002_initial_payments_sqlite.sql", "w") as f:
    f.write(payments_sql)

# Get all sqlite migrations
files = glob.glob("migrations/*_sqlite.sql")
files.sort()  # Sort by filename (timestamp/prefix)

print(f"Found {len(files)} migration files.")
for f in files:
    print(f"Preparation: {f}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Debug: check payments table
cursor.execute("PRAGMA table_info(payments)")
columns = cursor.fetchall()
print(f"Payments table columns before loop: {[col[1] for col in columns]}")

for f in files:
    print(f"Executing {f}...")
    try:
        with open(f, "r") as sql_file:
            sql_script = sql_file.read()
            cursor.executescript(sql_script)
            conn.commit()
    except Exception as e:
        print(f"Error executing {f}: {e}")
        conn.close()
        raise e

conn.close()
print("Database initialization completed.")
