-- AS-09: after-sales project tables (SQLite)
-- Targets: after_sales_* tables used by app/api/v1/endpoints/after_sales.py

BEGIN;

CREATE TABLE IF NOT EXISTS after_sales_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    feedback_type VARCHAR(30),
    feedback_content TEXT,
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'PENDING',
    assigned_to INTEGER,
    resolved_at DATETIME,
    resolution TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(assigned_to) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_asf_project ON after_sales_feedback(project_id);
CREATE INDEX IF NOT EXISTS idx_asf_customer ON after_sales_feedback(customer_id);
CREATE INDEX IF NOT EXISTS idx_asf_status ON after_sales_feedback(status);

CREATE TABLE IF NOT EXISTS after_sales_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    maintenance_type VARCHAR(30),
    maintenance_content TEXT,
    scheduled_date DATE,
    completed_date DATE,
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    technician_id INTEGER,
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(technician_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_asm_project ON after_sales_maintenance(project_id);
CREATE INDEX IF NOT EXISTS idx_asm_scheduled ON after_sales_maintenance(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_asm_status ON after_sales_maintenance(status);

CREATE TABLE IF NOT EXISTS after_sales_support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    ticket_no VARCHAR(50) UNIQUE,
    subject VARCHAR(200),
    description TEXT,
    category VARCHAR(30),
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'OPEN',
    assigned_to INTEGER,
    resolved_at DATETIME,
    resolution TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(assigned_to) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_asst_project ON after_sales_support_tickets(project_id);
CREATE INDEX IF NOT EXISTS idx_asst_ticket_no ON after_sales_support_tickets(ticket_no);
CREATE INDEX IF NOT EXISTS idx_asst_status ON after_sales_support_tickets(status);

CREATE TABLE IF NOT EXISTS after_sales_warranty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    warranty_no VARCHAR(50) UNIQUE,
    warranty_type VARCHAR(30),
    warranty_start DATE,
    warranty_end DATE,
    warranty_months INTEGER DEFAULT 12,
    scope TEXT,
    exclusions TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE INDEX IF NOT EXISTS idx_asw_project ON after_sales_warranty(project_id);
CREATE INDEX IF NOT EXISTS idx_asw_status ON after_sales_warranty(status);
CREATE INDEX IF NOT EXISTS idx_asw_end ON after_sales_warranty(warranty_end);

CREATE TABLE IF NOT EXISTS after_sales_spare_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    part_no VARCHAR(50),
    part_name VARCHAR(200),
    part_spec VARCHAR(500),
    quantity INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 1,
    unit_price NUMERIC(12, 2) DEFAULT 0,
    supplier VARCHAR(200),
    lead_time_days INTEGER,
    status VARCHAR(20) DEFAULT 'IN_STOCK',
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_assp_project ON after_sales_spare_parts(project_id);
CREATE INDEX IF NOT EXISTS idx_assp_status ON after_sales_spare_parts(status);

CREATE TABLE IF NOT EXISTS after_sales_field_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    ticket_id INTEGER,
    dispatch_order_id INTEGER,
    service_no VARCHAR(50) UNIQUE,
    service_type VARCHAR(30),
    service_content TEXT,
    planned_date DATE,
    actual_date DATE,
    service_hours INTEGER,
    travel_hours INTEGER,
    engineer_id INTEGER,
    engineer_name VARCHAR(100),
    travel_cost NUMERIC(12, 2) DEFAULT 0,
    parts_cost NUMERIC(12, 2) DEFAULT 0,
    service_fee NUMERIC(12, 2) DEFAULT 0,
    total_cost NUMERIC(12, 2) DEFAULT 0,
    is_warranty BOOLEAN DEFAULT 1,
    warranty_source VARCHAR(30),
    charge_required BOOLEAN DEFAULT 0,
    charge_reason VARCHAR(50),
    charge_status VARCHAR(20) DEFAULT 'NOT_REQUIRED',
    report_content TEXT,
    customer_sign BOOLEAN DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PLANNED',
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(ticket_id) REFERENCES after_sales_support_tickets(id),
    FOREIGN KEY(engineer_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_asfs_project ON after_sales_field_services(project_id);
CREATE INDEX IF NOT EXISTS idx_asfs_status ON after_sales_field_services(status);
CREATE INDEX IF NOT EXISTS idx_asfs_dispatch_order ON after_sales_field_services(dispatch_order_id);
CREATE INDEX IF NOT EXISTS idx_asfs_engineer ON after_sales_field_services(engineer_id);

CREATE TABLE IF NOT EXISTS after_sales_sla (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    ticket_id INTEGER,
    response_target_hours INTEGER DEFAULT 4,
    resolve_target_hours INTEGER DEFAULT 24,
    actual_response_hours INTEGER,
    actual_resolve_hours INTEGER,
    response_met BOOLEAN,
    resolve_met BOOLEAN,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(ticket_id) REFERENCES after_sales_support_tickets(id)
);
CREATE INDEX IF NOT EXISTS idx_sla_project ON after_sales_sla(project_id);
CREATE INDEX IF NOT EXISTS idx_sla_ticket ON after_sales_sla(ticket_id);

CREATE TABLE IF NOT EXISTS after_sales_satisfaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    customer_id INTEGER,
    ticket_id INTEGER,
    field_service_id INTEGER,
    overall_score INTEGER,
    response_score INTEGER,
    quality_score INTEGER,
    attitude_score INTEGER,
    nps_score INTEGER,
    comments TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(ticket_id) REFERENCES after_sales_support_tickets(id),
    FOREIGN KEY(field_service_id) REFERENCES after_sales_field_services(id)
);
CREATE INDEX IF NOT EXISTS idx_sat_project ON after_sales_satisfaction(project_id);

CREATE TABLE IF NOT EXISTS after_sales_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200),
    category VARCHAR(30),
    content TEXT,
    keywords VARCHAR(500),
    project_type VARCHAR(50),
    product_category VARCHAR(100),
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PUBLISHED',
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(created_by) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_ask_category ON after_sales_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_ask_status ON after_sales_knowledge(status);

COMMIT;
