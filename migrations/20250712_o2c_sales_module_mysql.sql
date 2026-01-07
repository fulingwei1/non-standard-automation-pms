-- Sales module migration (MySQL 8+)
-- Targets: leads/opportunities/quotes/contracts/invoices/disputes
-- Aligns with existing projects/payments tables.

-- 1) Leads
CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lead_code VARCHAR(20) UNIQUE NOT NULL,
    source VARCHAR(50),
    customer_name VARCHAR(100),
    industry VARCHAR(50),
    contact_name VARCHAR(50),
    contact_phone VARCHAR(20),
    demand_summary TEXT,
    owner_id INT,
    status VARCHAR(20) DEFAULT 'NEW',
    next_action_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_leads_owner (owner_id),
    CONSTRAINT fk_leads_owner FOREIGN KEY (owner_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Opportunities
CREATE TABLE IF NOT EXISTS opportunities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    opp_code VARCHAR(20) UNIQUE NOT NULL,
    lead_id INT,
    customer_id INT NOT NULL,
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
    score INT DEFAULT 0,
    risk_level VARCHAR(10),
    owner_id INT,
    gate_status VARCHAR(20) DEFAULT 'PENDING',
    gate_passed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_opportunities_customer (customer_id),
    INDEX idx_opportunities_owner (owner_id),
    CONSTRAINT fk_opportunities_lead FOREIGN KEY (lead_id) REFERENCES leads(id),
    CONSTRAINT fk_opportunities_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_opportunities_owner FOREIGN KEY (owner_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Opportunity requirements
CREATE TABLE IF NOT EXISTS opportunity_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    opportunity_id INT NOT NULL,
    product_object VARCHAR(100),
    ct_seconds INT,
    interface_desc TEXT,
    site_constraints TEXT,
    acceptance_criteria TEXT,
    safety_requirement TEXT,
    attachments TEXT,
    extra_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_opp_req_opportunity (opportunity_id),
    CONSTRAINT fk_opp_req_opportunity FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) Quotes
CREATE TABLE IF NOT EXISTS quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INT NOT NULL,
    customer_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    current_version_id INT,
    valid_until DATE,
    owner_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_quotes_opportunity (opportunity_id),
    CONSTRAINT fk_quotes_opportunity FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    CONSTRAINT fk_quotes_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_quotes_owner FOREIGN KEY (owner_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5) Quote versions
CREATE TABLE IF NOT EXISTS quote_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_id INT NOT NULL,
    version_no VARCHAR(10) NOT NULL,
    total_price DECIMAL(12,2),
    cost_total DECIMAL(12,2),
    gross_margin DECIMAL(5,2),
    lead_time_days INT,
    risk_terms TEXT,
    delivery_date DATE,
    created_by INT,
    approved_by INT,
    approved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_quote_version (quote_id, version_no),
    INDEX idx_quote_versions_quote (quote_id),
    CONSTRAINT fk_quote_versions_quote FOREIGN KEY (quote_id) REFERENCES quotes(id),
    CONSTRAINT fk_quote_versions_created_by FOREIGN KEY (created_by) REFERENCES employees(id),
    CONSTRAINT fk_quote_versions_approved_by FOREIGN KEY (approved_by) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6) Quote items
CREATE TABLE IF NOT EXISTS quote_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_version_id INT NOT NULL,
    item_type VARCHAR(20),
    item_name VARCHAR(200),
    qty DECIMAL(10,2),
    unit_price DECIMAL(12,2),
    cost DECIMAL(12,2),
    lead_time_days INT,
    remark TEXT,
    INDEX idx_quote_items_version (quote_version_id),
    CONSTRAINT fk_quote_items_version FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7) Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INT NOT NULL,
    quote_version_id INT,
    customer_id INT NOT NULL,
    project_id INT,
    contract_amount DECIMAL(12,2),
    signed_date DATE,
    status VARCHAR(20) DEFAULT 'DRAFT',
    payment_terms_summary TEXT,
    acceptance_summary TEXT,
    owner_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contracts_customer (customer_id),
    INDEX idx_contracts_project (project_id),
    CONSTRAINT fk_contracts_opportunity FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    CONSTRAINT fk_contracts_quote_version FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    CONSTRAINT fk_contracts_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_contracts_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_contracts_owner FOREIGN KEY (owner_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8) Contract deliverables
CREATE TABLE IF NOT EXISTS contract_deliverables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_id INT NOT NULL,
    deliverable_name VARCHAR(100),
    deliverable_type VARCHAR(50),
    required_for_payment BOOLEAN DEFAULT TRUE,
    template_ref VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract_deliverables_contract (contract_id),
    CONSTRAINT fk_contract_deliverables_contract FOREIGN KEY (contract_id) REFERENCES contracts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9) Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_code VARCHAR(30) UNIQUE NOT NULL,
    contract_id INT NOT NULL,
    project_id INT,
    payment_id INT,
    invoice_type VARCHAR(20),
    amount DECIMAL(12,2),
    tax_rate DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'DRAFT',
    issue_date DATE,
    buyer_name VARCHAR(100),
    buyer_tax_no VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_invoices_contract (contract_id),
    INDEX idx_invoices_payment (payment_id),
    CONSTRAINT fk_invoices_contract FOREIGN KEY (contract_id) REFERENCES contracts(id),
    CONSTRAINT fk_invoices_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_invoices_payment FOREIGN KEY (payment_id) REFERENCES payments(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10) Receivable disputes
CREATE TABLE IF NOT EXISTS receivable_disputes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    reason_code VARCHAR(30),
    description TEXT,
    status VARCHAR(20) DEFAULT 'OPEN',
    responsible_dept VARCHAR(50),
    responsible_id INT,
    expect_resolve_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_disputes_payment (payment_id),
    CONSTRAINT fk_disputes_payment FOREIGN KEY (payment_id) REFERENCES payments(id),
    CONSTRAINT fk_disputes_responsible FOREIGN KEY (responsible_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11) Extend payments for contract/milestone/deliverable/invoice linkage
ALTER TABLE payments ADD COLUMN contract_id INT;
ALTER TABLE payments ADD COLUMN milestone_id INT;
ALTER TABLE payments ADD COLUMN deliverable_id INT;
ALTER TABLE payments ADD COLUMN invoice_id INT;
ALTER TABLE payments ADD COLUMN responsible_id INT;
ALTER TABLE payments ADD COLUMN due_date DATE;

CREATE INDEX idx_payments_contract ON payments(contract_id);
CREATE INDEX idx_payments_milestone ON payments(milestone_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_responsible ON payments(responsible_id);
CREATE INDEX idx_payments_due_date ON payments(due_date);

-- Optional foreign keys (enable if corresponding tables exist and data is clean)
-- ALTER TABLE payments ADD CONSTRAINT fk_payments_contract FOREIGN KEY (contract_id) REFERENCES contracts(id);
-- ALTER TABLE payments ADD CONSTRAINT fk_payments_milestone FOREIGN KEY (milestone_id) REFERENCES milestones(id);
-- ALTER TABLE payments ADD CONSTRAINT fk_payments_deliverable FOREIGN KEY (deliverable_id) REFERENCES contract_deliverables(id);
-- ALTER TABLE payments ADD CONSTRAINT fk_payments_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id);
-- ALTER TABLE payments ADD CONSTRAINT fk_payments_responsible FOREIGN KEY (responsible_id) REFERENCES employees(id);
