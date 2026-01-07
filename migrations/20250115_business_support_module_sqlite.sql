-- ============================================
-- 商务支持模块数据库迁移
-- 创建日期: 2025-01-15
-- 说明: 创建商务支持模块相关表
-- ============================================

-- ============================================
-- 1. 投标项目表
-- ============================================
CREATE TABLE IF NOT EXISTS bidding_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bidding_no VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(500) NOT NULL,
    customer_id INTEGER,
    customer_name VARCHAR(200),
    
    -- 招标信息
    tender_no VARCHAR(100),
    tender_type VARCHAR(20),
    tender_platform VARCHAR(200),
    tender_url VARCHAR(500),
    
    -- 时间节点
    publish_date DATE,
    deadline_date DATETIME,
    bid_opening_date DATETIME,
    
    -- 标书信息
    bid_bond DECIMAL(15, 2),
    bid_bond_status VARCHAR(20) DEFAULT 'not_required',
    estimated_amount DECIMAL(15, 2),
    
    -- 投标准备
    bid_document_status VARCHAR(20) DEFAULT 'not_started',
    technical_doc_ready BOOLEAN DEFAULT 0,
    commercial_doc_ready BOOLEAN DEFAULT 0,
    qualification_doc_ready BOOLEAN DEFAULT 0,
    
    -- 投标方式
    submission_method VARCHAR(20),
    submission_address VARCHAR(500),
    
    -- 负责人
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    support_person_name VARCHAR(50),
    
    -- 投标结果
    bid_result VARCHAR(20) DEFAULT 'pending',
    bid_price DECIMAL(15, 2),
    win_price DECIMAL(15, 2),
    result_date DATE,
    result_remark TEXT,
    
    status VARCHAR(20) DEFAULT 'draft',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bidding_no ON bidding_projects(bidding_no);
CREATE INDEX IF NOT EXISTS idx_customer ON bidding_projects(customer_id);
CREATE INDEX IF NOT EXISTS idx_deadline ON bidding_projects(deadline_date);
CREATE INDEX IF NOT EXISTS idx_result ON bidding_projects(bid_result);

-- ============================================
-- 2. 投标文件表
-- ============================================
CREATE TABLE IF NOT EXISTS bidding_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bidding_project_id INTEGER NOT NULL,
    document_type VARCHAR(50),
    document_name VARCHAR(200),
    file_path VARCHAR(500),
    file_size INTEGER,
    version VARCHAR(20),
    status VARCHAR(20) DEFAULT 'draft',
    reviewed_by INTEGER,
    reviewed_at DATETIME,
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (bidding_project_id) REFERENCES bidding_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bidding_project ON bidding_documents(bidding_project_id);
CREATE INDEX IF NOT EXISTS idx_document_type ON bidding_documents(document_type);

-- ============================================
-- 3. 合同审核记录表
-- ============================================
CREATE TABLE IF NOT EXISTS contract_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    review_type VARCHAR(20),
    review_status VARCHAR(20) DEFAULT 'pending',
    reviewer_id INTEGER,
    review_comment TEXT,
    reviewed_at DATETIME,
    risk_items TEXT,  -- JSON格式
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_contract ON contract_reviews(contract_id);
CREATE INDEX IF NOT EXISTS idx_review_status ON contract_reviews(review_status);

-- ============================================
-- 4. 合同盖章邮寄记录表
-- ============================================
CREATE TABLE IF NOT EXISTS contract_seal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    seal_status VARCHAR(20) DEFAULT 'pending',
    seal_date DATE,
    seal_operator_id INTEGER,
    send_date DATE,
    tracking_no VARCHAR(50),
    courier_company VARCHAR(50),
    receive_date DATE,
    archive_date DATE,
    archive_location VARCHAR(200),
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (seal_operator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_contract_seal ON contract_seal_records(contract_id);
CREATE INDEX IF NOT EXISTS idx_seal_status ON contract_seal_records(seal_status);

-- ============================================
-- 5. 回款催收记录表
-- ============================================
CREATE TABLE IF NOT EXISTS payment_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    project_id INTEGER,
    payment_node VARCHAR(50),
    payment_amount DECIMAL(15, 2),
    plan_date DATE,
    reminder_type VARCHAR(20),
    reminder_content TEXT,
    reminder_date DATE,
    reminder_person_id INTEGER,
    customer_response TEXT,
    next_reminder_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reminder_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_contract_reminder ON payment_reminders(contract_id);
CREATE INDEX IF NOT EXISTS idx_project_reminder ON payment_reminders(project_id);
CREATE INDEX IF NOT EXISTS idx_reminder_date ON payment_reminders(reminder_date);

-- ============================================
-- 6. 文件归档表
-- ============================================
CREATE TABLE IF NOT EXISTS document_archives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archive_no VARCHAR(50) NOT NULL UNIQUE,
    document_type VARCHAR(50),
    related_type VARCHAR(50),
    related_id INTEGER,
    document_name VARCHAR(200),
    file_path VARCHAR(500),
    file_size INTEGER,
    archive_location VARCHAR(200),
    archive_date DATE,
    archiver_id INTEGER,
    status VARCHAR(20) DEFAULT 'archived',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (archiver_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_archive_no ON document_archives(archive_no);
CREATE INDEX IF NOT EXISTS idx_document_type_archive ON document_archives(document_type);
CREATE INDEX IF NOT EXISTS idx_related ON document_archives(related_type, related_id);

-- ============================================
-- 7. 销售订单表
-- ============================================
CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    contract_id INTEGER,
    contract_no VARCHAR(50),
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    project_id INTEGER,
    project_no VARCHAR(50),
    order_type VARCHAR(20) DEFAULT 'standard',
    order_amount DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'CNY',
    required_date DATE,
    promised_date DATE,
    order_status VARCHAR(20) DEFAULT 'draft',
    project_no_assigned BOOLEAN DEFAULT 0,
    project_no_assigned_date DATETIME,
    project_notice_sent BOOLEAN DEFAULT 0,
    project_notice_date DATETIME,
    erp_order_no VARCHAR(50),
    erp_sync_status VARCHAR(20) DEFAULT 'pending',
    erp_sync_time DATETIME,
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_order_no ON sales_orders(order_no);
CREATE INDEX IF NOT EXISTS idx_contract_order ON sales_orders(contract_id);
CREATE INDEX IF NOT EXISTS idx_customer_order ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_project_order ON sales_orders(project_id);
CREATE INDEX IF NOT EXISTS idx_status_order ON sales_orders(order_status);

-- ============================================
-- 8. 销售订单明细表
-- ============================================
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL,
    item_name VARCHAR(200),
    item_spec VARCHAR(200),
    qty DECIMAL(10, 2),
    unit VARCHAR(20),
    unit_price DECIMAL(12, 2),
    amount DECIMAL(12, 2),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sales_order_item ON sales_order_items(sales_order_id);

-- ============================================
-- 9. 发货单表
-- ============================================
CREATE TABLE IF NOT EXISTS delivery_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_no VARCHAR(50) NOT NULL UNIQUE,
    order_id INTEGER NOT NULL,
    order_no VARCHAR(50),
    contract_id INTEGER,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    project_id INTEGER,
    delivery_date DATE,
    delivery_type VARCHAR(20),
    logistics_company VARCHAR(100),
    tracking_no VARCHAR(100),
    receiver_name VARCHAR(50),
    receiver_phone VARCHAR(20),
    receiver_address VARCHAR(500),
    delivery_amount DECIMAL(15, 2),
    approval_status VARCHAR(20) DEFAULT 'pending',
    approval_comment TEXT,
    approved_by INTEGER,
    approved_at DATETIME,
    special_approval BOOLEAN DEFAULT 0,
    special_approver_id INTEGER,
    special_approval_reason TEXT,
    delivery_status VARCHAR(20) DEFAULT 'draft',
    print_date DATETIME,
    ship_date DATETIME,
    receive_date DATE,
    return_status VARCHAR(20) DEFAULT 'pending',
    return_date DATE,
    signed_delivery_file_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (special_approver_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_delivery_no ON delivery_orders(delivery_no);
CREATE INDEX IF NOT EXISTS idx_order_delivery ON delivery_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_customer_delivery ON delivery_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_status_delivery ON delivery_orders(delivery_status);
CREATE INDEX IF NOT EXISTS idx_return_status ON delivery_orders(return_status);

-- ============================================
-- 10. 验收单跟踪表（商务支持角度）
-- ============================================
CREATE TABLE IF NOT EXISTS acceptance_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acceptance_order_id INTEGER NOT NULL,
    acceptance_order_no VARCHAR(50),
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    condition_check_status VARCHAR(20) DEFAULT 'pending',
    condition_check_result TEXT,
    condition_check_date DATETIME,
    condition_checker_id INTEGER,
    tracking_status VARCHAR(20) DEFAULT 'pending',
    reminder_count INTEGER DEFAULT 0,
    last_reminder_date DATETIME,
    last_reminder_by INTEGER,
    received_date DATE,
    signed_file_id INTEGER,
    report_status VARCHAR(20) DEFAULT 'pending',
    report_generated_date DATETIME,
    report_signed_date DATETIME,
    report_archived_date DATETIME,
    warranty_start_date DATE,
    warranty_end_date DATE,
    warranty_status VARCHAR(20) DEFAULT 'not_started',
    warranty_expiry_reminded BOOLEAN DEFAULT 0,
    contract_id INTEGER,
    contract_no VARCHAR(50),
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (condition_checker_id) REFERENCES users(id),
    FOREIGN KEY (last_reminder_by) REFERENCES users(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_acceptance_order_tracking ON acceptance_tracking(acceptance_order_id);
CREATE INDEX IF NOT EXISTS idx_project_tracking ON acceptance_tracking(project_id);
CREATE INDEX IF NOT EXISTS idx_customer_tracking ON acceptance_tracking(customer_id);
CREATE INDEX IF NOT EXISTS idx_tracking_status ON acceptance_tracking(tracking_status);
CREATE INDEX IF NOT EXISTS idx_condition_status ON acceptance_tracking(condition_check_status);

-- ============================================
-- 11. 验收单跟踪记录明细表
-- ============================================
CREATE TABLE IF NOT EXISTS acceptance_tracking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_id INTEGER NOT NULL,
    record_type VARCHAR(20) NOT NULL,
    record_content TEXT,
    record_date DATETIME NOT NULL,
    operator_id INTEGER NOT NULL,
    operator_name VARCHAR(50),
    result VARCHAR(20),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracking_id) REFERENCES acceptance_tracking(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_tracking_record ON acceptance_tracking_records(tracking_id);
CREATE INDEX IF NOT EXISTS idx_record_type ON acceptance_tracking_records(record_type);
CREATE INDEX IF NOT EXISTS idx_record_date ON acceptance_tracking_records(record_date);

-- ============================================
-- 12. 客户对账单表
-- ============================================
CREATE TABLE IF NOT EXISTS reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_no VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    period_start DATE,
    period_end DATE,
    opening_balance DECIMAL(15, 2) DEFAULT 0,
    period_sales DECIMAL(15, 2) DEFAULT 0,
    period_receipt DECIMAL(15, 2) DEFAULT 0,
    closing_balance DECIMAL(15, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    sent_date DATE,
    confirm_date DATE,
    customer_confirmed BOOLEAN DEFAULT 0,
    customer_confirm_date DATE,
    customer_difference DECIMAL(15, 2),
    difference_reason TEXT,
    reconciliation_file_id INTEGER,
    confirmed_file_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_no ON reconciliations(reconciliation_no);
CREATE INDEX IF NOT EXISTS idx_customer_reconciliation ON reconciliations(customer_id);
CREATE INDEX IF NOT EXISTS idx_period ON reconciliations(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_status_reconciliation ON reconciliations(status);

