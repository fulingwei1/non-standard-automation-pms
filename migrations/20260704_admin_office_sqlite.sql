-- ADMIN-07: 行政管理做实（用品/申领/车辆/用车/资产/费用真表）。

CREATE TABLE IF NOT EXISTS admin_supplies (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    specification VARCHAR(200),
    unit VARCHAR(20) DEFAULT '件',
    current_stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    unit_price NUMERIC(10,2) DEFAULT 0,
    supplier VARCHAR(100),
    last_purchase_date DATE,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS admin_supply_requests (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    supply_id INTEGER NOT NULL REFERENCES admin_supplies(id),
    quantity INTEGER NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    requested_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at DATETIME,
    approval_comment TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS admin_vehicles (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    plate_no VARCHAR(20) NOT NULL UNIQUE,
    model VARCHAR(100),
    seats INTEGER,
    status VARCHAR(20) DEFAULT 'AVAILABLE',
    current_driver VARCHAR(50),
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS admin_vehicle_requests (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER REFERENCES admin_vehicles(id),
    use_date DATE NOT NULL,
    destination VARCHAR(200),
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    requested_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at DATETIME,
    approval_comment TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS admin_assets (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    asset_no VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    specification VARCHAR(200),
    value NUMERIC(12,2) DEFAULT 0,
    purchase_date DATE,
    custodian VARCHAR(50),
    location VARCHAR(100),
    status VARCHAR(20) DEFAULT 'IN_USE',
    remark TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS admin_expenses (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    expense_no VARCHAR(50) UNIQUE,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    expense_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'RECORDED',
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_admin_supply_req_status ON admin_supply_requests (status);
CREATE INDEX IF NOT EXISTS idx_admin_vehicle_req_status ON admin_vehicle_requests (status);
CREATE INDEX IF NOT EXISTS idx_admin_expense_date ON admin_expenses (expense_date);
