import glob
import os
import sqlite3

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

# First, create all tables using SQLAlchemy models
print("Creating tables using SQLAlchemy models...")
try:
    from app.models.base import Base, engine
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
except Exception as e:
    print(f"Warning: Error creating tables: {e}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Disable foreign key checks during migration
cursor.execute("PRAGMA foreign_keys = OFF")

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

# Re-enable foreign key checks
cursor.execute("PRAGMA foreign_keys = ON")
conn.close()
print("Database migration execution completed.")

# Seed initial data (Admin User)
print("Seeding initial data...")
try:
    from app.core import security
    from app.models.base import get_session
    from app.models.organization import Employee
    from app.models.user import User

    with get_session() as db:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Create an employee for admin
            emp = Employee(
                employee_code="E0001",
                name="System Admin",
                department="IT",
                role="ADMIN",
            )
            db.add(emp)
            db.flush()  # Get emp.id

            # Create the user
            user = User(
                username="admin",
                employee_id=emp.id,
                password_hash=security.get_password_hash("password123"),
                real_name="System Admin",
                is_active=True,
                is_superuser=True,
                auth_type="password",
            )
            db.add(user)
            db.commit()
            print("Default admin user created: admin / [请查看环境变量或配置文件]")
        else:
            print("Admin user already exists.")
except Exception as e:
    print(f"Error seeding initial data: {e}")

print("Database initialization completed.")
