-- Installation Dispatch module migration (SQLite)
-- Creates installation_dispatch_orders table

-- PRAGMA foreign_keys = ON;  -- Disabled for migration
BEGIN;

-- Installation Dispatch Orders Table
CREATE TABLE IF NOT EXISTS installation_dispatch_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    customer_id INTEGER NOT NULL,
    task_type VARCHAR(20) NOT NULL,
    task_title VARCHAR(200) NOT NULL,
    task_description TEXT,
    location VARCHAR(200),
    scheduled_date DATE NOT NULL,
    estimated_hours NUMERIC(5, 2),
    assigned_to_id INTEGER,
    assigned_to_name VARCHAR(50),
    assigned_by_id INTEGER,
    assigned_by_name VARCHAR(50),
    assigned_time DATETIME,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    actual_hours NUMERIC(5, 2),
    progress INTEGER DEFAULT 0,
    customer_contact VARCHAR(50),
    customer_phone VARCHAR(20),
    customer_address VARCHAR(500),
    execution_notes TEXT,
    issues_found TEXT,
    solution_provided TEXT,
    photos TEXT,  -- JSON format
    service_record_id INTEGER,
    acceptance_order_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (assigned_to_id) REFERENCES users(id),
    FOREIGN KEY (assigned_by_id) REFERENCES users(id),
    FOREIGN KEY (service_record_id) REFERENCES service_records(id),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id)
);

CREATE INDEX IF NOT EXISTS idx_install_dispatch_project ON installation_dispatch_orders(project_id);
CREATE INDEX IF NOT EXISTS idx_install_dispatch_machine ON installation_dispatch_orders(machine_id);
CREATE INDEX IF NOT EXISTS idx_install_dispatch_customer ON installation_dispatch_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_install_dispatch_status ON installation_dispatch_orders(status);
CREATE INDEX IF NOT EXISTS idx_install_dispatch_assigned ON installation_dispatch_orders(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_install_dispatch_date ON installation_dispatch_orders(scheduled_date);

COMMIT;
