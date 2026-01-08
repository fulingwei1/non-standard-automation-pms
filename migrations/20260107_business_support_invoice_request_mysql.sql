-- ============================================
-- 商务支持模块 - 开票申请与客户入驻 - MySQL 数据库迁移
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 新增开票申请表、客户供应商入驻管理表
-- ============================================

-- ============================================
-- 1. 开票申请表
-- ============================================

CREATE TABLE IF NOT EXISTS invoice_requests (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_no          VARCHAR(50) NOT NULL UNIQUE,
    contract_id         BIGINT NOT NULL,
    project_id          BIGINT,
    project_name        VARCHAR(200),
    customer_id         BIGINT NOT NULL,
    customer_name       VARCHAR(200),
    payment_plan_id     BIGINT,
    invoice_type        VARCHAR(20),
    invoice_title       VARCHAR(200),
    tax_rate            DECIMAL(5,2),
    amount              DECIMAL(14,2) NOT NULL,
    tax_amount          DECIMAL(14,2),
    total_amount        DECIMAL(14,2),
    currency            VARCHAR(10) DEFAULT 'CNY',
    expected_issue_date DATE,
    expected_payment_date DATE,
    reason              TEXT,
    attachments         TEXT,
    remark              TEXT,
    status              VARCHAR(20) DEFAULT 'PENDING',
    approval_comment    TEXT,
    requested_by        BIGINT NOT NULL,
    requested_by_name   VARCHAR(50),
    approved_by         BIGINT,
    approved_at         DATETIME,
    invoice_id          BIGINT,
    receipt_status      VARCHAR(20) DEFAULT 'UNPAID',
    receipt_updated_at  DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_invoice_request_contract FOREIGN KEY (contract_id) REFERENCES contracts(id),
    CONSTRAINT fk_invoice_request_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_invoice_request_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_invoice_request_plan FOREIGN KEY (payment_plan_id) REFERENCES project_payment_plans(id),
    CONSTRAINT fk_invoice_request_requester FOREIGN KEY (requested_by) REFERENCES users(id),
    CONSTRAINT fk_invoice_request_approver FOREIGN KEY (approved_by) REFERENCES users(id),
    CONSTRAINT fk_invoice_request_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开票申请表';

CREATE INDEX idx_invoice_request_contract ON invoice_requests(contract_id);
CREATE INDEX idx_invoice_request_project ON invoice_requests(project_id);
CREATE INDEX idx_invoice_request_customer ON invoice_requests(customer_id);
CREATE INDEX idx_invoice_request_status ON invoice_requests(status);
CREATE INDEX idx_invoice_request_plan ON invoice_requests(payment_plan_id);

-- ============================================
-- 2. 客户供应商入驻表
-- ============================================

CREATE TABLE IF NOT EXISTS customer_supplier_registrations (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    registration_no     VARCHAR(100) NOT NULL UNIQUE,
    customer_id         BIGINT NOT NULL,
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
    reviewer_id         BIGINT,
    review_comment      TEXT,
    external_sync_status VARCHAR(20) DEFAULT 'pending',
    last_sync_at        DATETIME,
    sync_message        TEXT,
    remark              TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_supplier_reg_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_supplier_reg_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户供应商入驻表';

CREATE INDEX idx_supplier_reg_customer ON customer_supplier_registrations(customer_id);
CREATE INDEX idx_supplier_reg_platform ON customer_supplier_registrations(platform_name);
CREATE INDEX idx_supplier_reg_status ON customer_supplier_registrations(registration_status);

