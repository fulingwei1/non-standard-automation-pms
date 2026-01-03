-- Sales module migration (SQLite)
-- Targets: leads/opportunities/quotes/contracts/invoices/disputes
-- Aligns with existing projects/payments tables.

PRAGMA foreign_keys = ON;
BEGIN;

-- 1) Leads
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_code VARCHAR(20) UNIQUE NOT NULL,
    source VARCHAR(50),
    customer_name VARCHAR(100),
    industry VARCHAR(50),
    contact_name VARCHAR(50),
    contact_phone VARCHAR(20),
    demand_summary TEXT,
    owner_id INTEGER,
    status VARCHAR(20) DEFAULT 'NEW',
    next_action_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);

-- 2) Opportunities
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opp_code VARCHAR(20) UNIQUE NOT NULL,
    lead_id INTEGER,
    customer_id INTEGER NOT NULL,
    opp_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(20),
    equipment_type VARCHAR(20),
    stage VARCHAR(20) DEFAULT 'DISCOVERY',
    est_amount DECIMAL(12,2),
    est_margin DECIMAL(5,2),
    budget_range VARCHAR(50),
    decision_chain TEXT,
    delivery_window VARCHAR(50),
    acceptance_basis TEXT,
    score INTEGER DEFAULT 0,
    risk_level VARCHAR(10),
    owner_id INTEGER,
    gate_status VARCHAR(20) DEFAULT 'PENDING',
    gate_passed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);

-- 3) Opportunity requirements
CREATE TABLE IF NOT EXISTS opportunity_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    product_object VARCHAR(100),
    ct_seconds INTEGER,
    interface_desc TEXT,
    site_constraints TEXT,
    acceptance_criteria TEXT,
    safety_requirement TEXT,
    attachments TEXT,
    extra_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

-- 4) Quotes
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    current_version_id INTEGER,
    valid_until DATE,
    owner_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);

-- 5) Quote versions
CREATE TABLE IF NOT EXISTS quote_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    version_no VARCHAR(10) NOT NULL,
    total_price DECIMAL(12,2),
    cost_total DECIMAL(12,2),
    gross_margin DECIMAL(5,2),
    lead_time_days INTEGER,
    risk_terms TEXT,
    delivery_date DATE,
    created_by INTEGER,
    approved_by INTEGER,
    approved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (created_by) REFERENCES employees(id),
    FOREIGN KEY (approved_by) REFERENCES employees(id)
);

-- 6) Quote items
CREATE TABLE IF NOT EXISTS quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_version_id INTEGER NOT NULL,
    item_type VARCHAR(20),
    item_name VARCHAR(200),
    qty DECIMAL(10,2),
    unit_price DECIMAL(12,2),
    cost DECIMAL(12,2),
    lead_time_days INTEGER,
    remark TEXT,
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id)
);

-- 7) Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INTEGER NOT NULL,
    quote_version_id INTEGER,
    customer_id INTEGER NOT NULL,
    project_id INTEGER,
    contract_amount DECIMAL(12,2),
    signed_date DATE,
    status VARCHAR(20) DEFAULT 'DRAFT',
    payment_terms_summary TEXT,
    acceptance_summary TEXT,
    owner_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);

-- 8) Contract deliverables
CREATE TABLE IF NOT EXISTS contract_deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    deliverable_name VARCHAR(100),
    deliverable_type VARCHAR(50),
    required_for_payment BOOLEAN DEFAULT TRUE,
    template_ref VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- 9) Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_code VARCHAR(30) UNIQUE NOT NULL,
    contract_id INTEGER NOT NULL,
    project_id INTEGER,
    payment_id INTEGER,
    invoice_type VARCHAR(20),
    amount DECIMAL(12,2),
    tax_rate DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'DRAFT',
    issue_date DATE,
    buyer_name VARCHAR(100),
    buyer_tax_no VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);

-- 10) Receivable disputes
CREATE TABLE IF NOT EXISTS receivable_disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL,
    reason_code VARCHAR(30),
    description TEXT,
    status VARCHAR(20) DEFAULT 'OPEN',
    responsible_dept VARCHAR(50),
    responsible_id INTEGER,
    expect_resolve_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payments(id),
    FOREIGN KEY (responsible_id) REFERENCES employees(id)
);

-- 11) Extend payments for contract/milestone/deliverable/invoice linkage
ALTER TABLE payments ADD COLUMN contract_id INTEGER;
ALTER TABLE payments ADD COLUMN milestone_id INTEGER;
ALTER TABLE payments ADD COLUMN deliverable_id INTEGER;
ALTER TABLE payments ADD COLUMN invoice_id INTEGER;
ALTER TABLE payments ADD COLUMN responsible_id INTEGER;
ALTER TABLE payments ADD COLUMN due_date DATE;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_leads_owner ON leads(owner_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_customer ON opportunities(customer_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX IF NOT EXISTS idx_quotes_opportunity ON quotes(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_quote_versions_quote ON quote_versions(quote_id);
CREATE INDEX IF NOT EXISTS idx_quote_items_version ON quote_items(quote_version_id);
CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contracts_project ON contracts(project_id);
CREATE INDEX IF NOT EXISTS idx_invoices_contract ON invoices(contract_id);
CREATE INDEX IF NOT EXISTS idx_invoices_payment ON invoices(payment_id);
CREATE INDEX IF NOT EXISTS idx_disputes_payment ON receivable_disputes(payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_contract ON payments(contract_id);
CREATE INDEX IF NOT EXISTS idx_payments_milestone ON payments(milestone_id);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_responsible ON payments(responsible_id);
CREATE INDEX IF NOT EXISTS idx_payments_due_date ON payments(due_date);

COMMIT;
