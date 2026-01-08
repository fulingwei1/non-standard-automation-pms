-- ============================================
-- 商务支持模块 - 开票申请与客户入驻 - SQLite 数据库迁移
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 新增开票申请表、客户供应商入驻管理表
-- ============================================

-- ============================================
-- 1. 开票申请表
-- ============================================

CREATE TABLE IF NOT EXISTS invoice_requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_no          VARCHAR(50) NOT NULL UNIQUE,
    contract_id         INTEGER NOT NULL,
    project_id          INTEGER,
    project_name        VARCHAR(200),
    customer_id         INTEGER NOT NULL,
    customer_name       VARCHAR(200),
    payment_plan_id     INTEGER,
    invoice_type        VARCHAR(20),
    invoice_title       VARCHAR(200),
    tax_rate            NUMERIC(5, 2),
    amount              NUMERIC(14, 2) NOT NULL,
    tax_amount          NUMERIC(14, 2),
    total_amount        NUMERIC(14, 2),
    currency            VARCHAR(10) DEFAULT 'CNY',
    expected_issue_date DATE,
    expected_payment_date DATE,
    reason              TEXT,
    attachments         TEXT,
    remark              TEXT,
    status              VARCHAR(20) DEFAULT 'PENDING',
    approval_comment    TEXT,
    requested_by        INTEGER NOT NULL,
    requested_by_name   VARCHAR(50),
    approved_by         INTEGER,
    approved_at         DATETIME,
    invoice_id          INTEGER,
    receipt_status      VARCHAR(20) DEFAULT 'UNPAID',
    receipt_updated_at  DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (payment_plan_id) REFERENCES project_payment_plans(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

CREATE INDEX idx_invoice_request_no ON invoice_requests(request_no);
CREATE INDEX idx_invoice_request_contract ON invoice_requests(contract_id);
CREATE INDEX idx_invoice_request_project ON invoice_requests(project_id);
CREATE INDEX idx_invoice_request_customer ON invoice_requests(customer_id);
CREATE INDEX idx_invoice_request_status ON invoice_requests(status);
CREATE INDEX idx_invoice_request_plan ON invoice_requests(payment_plan_id);

-- ============================================
-- 2. 客户供应商入驻表
-- ============================================

CREATE TABLE IF NOT EXISTS customer_supplier_registrations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_no     VARCHAR(100) NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL,
    customer_name       VARCHAR(200),
    platform_name       VARCHAR(100) NOT NULL,
    platform_url        VARCHAR(500),
    registration_status VARCHAR(20) DEFAULT 'PENDING',
    application_date    DATE,
    approved_date       DATE,
    expire_date         DATE,
    contact_person      VARCHAR(50),
    contact_phone       VARCHAR(30),
    contact_email       VARCHAR(100),
    required_docs       TEXT,
    reviewer_id         INTEGER,
    review_comment      TEXT,
    external_sync_status VARCHAR(20) DEFAULT 'pending',
    last_sync_at        DATETIME,
    sync_message        TEXT,
    remark              TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX idx_supplier_reg_customer ON customer_supplier_registrations(customer_id);
CREATE INDEX idx_supplier_reg_platform ON customer_supplier_registrations(platform_name);
CREATE INDEX idx_supplier_reg_status ON customer_supplier_registrations(registration_status);

