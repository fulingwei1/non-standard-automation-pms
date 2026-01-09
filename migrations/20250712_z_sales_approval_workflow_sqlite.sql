-- ============================================
-- 销售模块多级审批工作流迁移
-- 添加审批表
-- ============================================

-- 1) 报价审批表
CREATE TABLE IF NOT EXISTS quote_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 2) 合同审批表
CREATE TABLE IF NOT EXISTS contract_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 3) 发票审批表
CREATE TABLE IF NOT EXISTS invoice_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_quote_approval_quote ON quote_approvals(quote_id);
CREATE INDEX IF NOT EXISTS idx_quote_approval_approver ON quote_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_quote_approval_status ON quote_approvals(status);

CREATE INDEX IF NOT EXISTS idx_contract_approval_contract ON contract_approvals(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_approval_approver ON contract_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_contract_approval_status ON contract_approvals(status);

CREATE INDEX IF NOT EXISTS idx_invoice_approval_invoice ON invoice_approvals(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_approval_approver ON invoice_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_invoice_approval_status ON invoice_approvals(status);



