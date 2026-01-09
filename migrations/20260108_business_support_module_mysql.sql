-- ============================================
-- 商务支持模块数据库迁移 (MySQL)
-- 创建日期: 2025-01-15
-- 说明: 创建商务支持模块相关表
-- ============================================

-- ============================================
-- 1. 投标项目表
-- ============================================
CREATE TABLE IF NOT EXISTS bidding_projects (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    bidding_no VARCHAR(50) NOT NULL UNIQUE COMMENT '投标编号',
    project_name VARCHAR(500) NOT NULL COMMENT '项目名称',
    customer_id INT UNSIGNED COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    
    -- 招标信息
    tender_no VARCHAR(100) COMMENT '招标编号',
    tender_type VARCHAR(20) COMMENT '招标类型：public/invited/competitive/single_source/online',
    tender_platform VARCHAR(200) COMMENT '招标平台',
    tender_url VARCHAR(500) COMMENT '招标链接',
    
    -- 时间节点
    publish_date DATE COMMENT '发布日期',
    deadline_date DATETIME COMMENT '投标截止时间',
    bid_opening_date DATETIME COMMENT '开标时间',
    
    -- 标书信息
    bid_bond DECIMAL(15, 2) COMMENT '投标保证金',
    bid_bond_status VARCHAR(20) DEFAULT 'not_required' COMMENT '保证金状态：not_required/pending/paid/returned',
    estimated_amount DECIMAL(15, 2) COMMENT '预估金额',
    
    -- 投标准备
    bid_document_status VARCHAR(20) DEFAULT 'not_started' COMMENT '标书状态：not_started/in_progress/completed/submitted',
    technical_doc_ready TINYINT(1) DEFAULT 0 COMMENT '技术文件就绪',
    commercial_doc_ready TINYINT(1) DEFAULT 0 COMMENT '商务文件就绪',
    qualification_doc_ready TINYINT(1) DEFAULT 0 COMMENT '资质文件就绪',
    
    -- 投标方式
    submission_method VARCHAR(20) COMMENT '投递方式：offline/online/both',
    submission_address VARCHAR(500) COMMENT '投递地址',
    
    -- 负责人
    sales_person_id INT UNSIGNED COMMENT '业务员ID',
    sales_person_name VARCHAR(50) COMMENT '业务员',
    support_person_id INT UNSIGNED COMMENT '商务支持ID',
    support_person_name VARCHAR(50) COMMENT '商务支持',
    
    -- 投标结果
    bid_result VARCHAR(20) DEFAULT 'pending' COMMENT '投标结果：pending/won/lost/cancelled/invalid',
    bid_price DECIMAL(15, 2) COMMENT '投标价格',
    win_price DECIMAL(15, 2) COMMENT '中标价格',
    result_date DATE COMMENT '结果公布日期',
    result_remark TEXT COMMENT '结果说明',
    
    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft/preparing/submitted/closed',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_bidding_no (bidding_no),
    INDEX idx_customer (customer_id),
    INDEX idx_deadline (deadline_date),
    INDEX idx_result (bid_result),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (sales_person_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (support_person_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投标项目表';

-- ============================================
-- 2. 投标文件表
-- ============================================
CREATE TABLE IF NOT EXISTS bidding_documents (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    bidding_project_id INT UNSIGNED NOT NULL COMMENT '投标项目ID',
    document_type VARCHAR(50) COMMENT '文件类型：technical/commercial/qualification/other',
    document_name VARCHAR(200) COMMENT '文件名称',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_size INT UNSIGNED COMMENT '文件大小(字节)',
    version VARCHAR(20) COMMENT '版本号',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft/reviewed/approved',
    reviewed_by INT UNSIGNED COMMENT '审核人ID',
    reviewed_at DATETIME COMMENT '审核时间',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_bidding_project (bidding_project_id),
    INDEX idx_document_type (document_type),
    FOREIGN KEY (bidding_project_id) REFERENCES bidding_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投标文件表';

-- ============================================
-- 3. 合同审核记录表
-- ============================================
CREATE TABLE IF NOT EXISTS contract_reviews (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id INT UNSIGNED NOT NULL COMMENT '合同ID',
    review_type VARCHAR(20) COMMENT '审核类型：business/legal/finance',
    review_status VARCHAR(20) DEFAULT 'pending' COMMENT '审核状态：pending/passed/rejected',
    reviewer_id INT UNSIGNED COMMENT '审核人ID',
    review_comment TEXT COMMENT '审核意见',
    reviewed_at DATETIME COMMENT '审核时间',
    risk_items JSON COMMENT '风险项列表',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_contract (contract_id),
    INDEX idx_review_status (review_status),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同审核记录表';

-- ============================================
-- 4. 合同盖章邮寄记录表
-- ============================================
CREATE TABLE IF NOT EXISTS contract_seal_records (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id INT UNSIGNED NOT NULL COMMENT '合同ID',
    seal_status VARCHAR(20) DEFAULT 'pending' COMMENT '盖章状态：pending/sealed/sent/received/archived',
    seal_date DATE COMMENT '盖章日期',
    seal_operator_id INT UNSIGNED COMMENT '盖章操作人ID',
    send_date DATE COMMENT '邮寄日期',
    tracking_no VARCHAR(50) COMMENT '快递单号',
    courier_company VARCHAR(50) COMMENT '快递公司',
    receive_date DATE COMMENT '回收日期',
    archive_date DATE COMMENT '归档日期',
    archive_location VARCHAR(200) COMMENT '归档位置',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_contract_seal (contract_id),
    INDEX idx_seal_status (seal_status),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (seal_operator_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同盖章邮寄记录表';

-- ============================================
-- 5. 回款催收记录表
-- ============================================
CREATE TABLE IF NOT EXISTS payment_reminders (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id INT UNSIGNED NOT NULL COMMENT '合同ID',
    project_id INT UNSIGNED COMMENT '项目ID',
    payment_node VARCHAR(50) COMMENT '付款节点：prepayment/delivery/acceptance/warranty',
    payment_amount DECIMAL(15, 2) COMMENT '应回款金额',
    plan_date DATE COMMENT '计划回款日期',
    reminder_type VARCHAR(20) COMMENT '催收类型：call/email/visit/other',
    reminder_content TEXT COMMENT '催收内容',
    reminder_date DATE COMMENT '催收日期',
    reminder_person_id INT UNSIGNED COMMENT '催收人ID',
    customer_response TEXT COMMENT '客户反馈',
    next_reminder_date DATE COMMENT '下次催收日期',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/completed/cancelled',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_contract_reminder (contract_id),
    INDEX idx_project_reminder (project_id),
    INDEX idx_reminder_date (reminder_date),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (reminder_person_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回款催收记录表';

-- ============================================
-- 6. 文件归档表
-- ============================================
CREATE TABLE IF NOT EXISTS document_archives (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    archive_no VARCHAR(50) NOT NULL UNIQUE COMMENT '归档编号',
    document_type VARCHAR(50) COMMENT '文件类型：contract/acceptance/invoice/other',
    related_type VARCHAR(50) COMMENT '关联类型：contract/project/acceptance',
    related_id INT UNSIGNED COMMENT '关联ID',
    document_name VARCHAR(200) COMMENT '文件名称',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_size INT UNSIGNED COMMENT '文件大小(字节)',
    archive_location VARCHAR(200) COMMENT '归档位置',
    archive_date DATE COMMENT '归档日期',
    archiver_id INT UNSIGNED COMMENT '归档人ID',
    status VARCHAR(20) DEFAULT 'archived' COMMENT '状态：archived/borrowed/returned',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    INDEX idx_archive_no (archive_no),
    INDEX idx_document_type_archive (document_type),
    INDEX idx_related (related_type, related_id),
    FOREIGN KEY (archiver_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件归档表';

-- ============================================
-- 7. 销售订单表
-- ============================================
CREATE TABLE IF NOT EXISTS sales_orders (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_no VARCHAR(50) NOT NULL UNIQUE COMMENT '订单编号',
    contract_id INT UNSIGNED COMMENT '合同ID',
    contract_no VARCHAR(50) COMMENT '合同编号',
    customer_id INT UNSIGNED NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    project_id INT UNSIGNED COMMENT '项目ID',
    project_no VARCHAR(50) COMMENT '项目号',
    order_type VARCHAR(20) DEFAULT 'standard' COMMENT '订单类型：standard/sample/repair/other',
    order_amount DECIMAL(15, 2) COMMENT '订单金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    required_date DATE COMMENT '客户要求日期',
    promised_date DATE COMMENT '承诺交期',
    order_status VARCHAR(20) DEFAULT 'draft' COMMENT '订单状态：draft/confirmed/in_production/ready/partial_shipped/shipped/completed/cancelled',
    project_no_assigned TINYINT(1) DEFAULT 0 COMMENT '是否已分配项目号',
    project_no_assigned_date DATETIME COMMENT '项目号分配时间',
    project_notice_sent TINYINT(1) DEFAULT 0 COMMENT '是否已发项目通知单',
    project_notice_date DATETIME COMMENT '通知单发布时间',
    erp_order_no VARCHAR(50) COMMENT 'ERP订单号',
    erp_sync_status VARCHAR(20) DEFAULT 'pending' COMMENT 'ERP同步状态：pending/synced/failed',
    erp_sync_time DATETIME COMMENT 'ERP同步时间',
    sales_person_id INT UNSIGNED COMMENT '业务员ID',
    sales_person_name VARCHAR(50) COMMENT '业务员',
    support_person_id INT UNSIGNED COMMENT '商务支持ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_order_no (order_no),
    INDEX idx_contract_order (contract_id),
    INDEX idx_customer_order (customer_id),
    INDEX idx_project_order (project_id),
    INDEX idx_status_order (order_status),
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (sales_person_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (support_person_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='销售订单表';

-- ============================================
-- 8. 销售订单明细表
-- ============================================
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    sales_order_id INT UNSIGNED NOT NULL COMMENT '销售订单ID',
    item_name VARCHAR(200) COMMENT '明细名称',
    item_spec VARCHAR(200) COMMENT '规格型号',
    qty DECIMAL(10, 2) COMMENT '数量',
    unit VARCHAR(20) COMMENT '单位',
    unit_price DECIMAL(12, 2) COMMENT '单价',
    amount DECIMAL(12, 2) COMMENT '金额',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_sales_order_item (sales_order_id),
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='销售订单明细表';

-- ============================================
-- 9. 发货单表
-- ============================================
CREATE TABLE IF NOT EXISTS delivery_orders (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    delivery_no VARCHAR(50) NOT NULL UNIQUE COMMENT '送货单号',
    order_id INT UNSIGNED NOT NULL COMMENT '销售订单ID',
    order_no VARCHAR(50) COMMENT '销售订单号',
    contract_id INT UNSIGNED COMMENT '合同ID',
    customer_id INT UNSIGNED NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    project_id INT UNSIGNED COMMENT '项目ID',
    delivery_date DATE COMMENT '发货日期',
    delivery_type VARCHAR(20) COMMENT '发货方式：express/logistics/self_pickup/install',
    logistics_company VARCHAR(100) COMMENT '物流公司',
    tracking_no VARCHAR(100) COMMENT '物流单号',
    receiver_name VARCHAR(50) COMMENT '收货人',
    receiver_phone VARCHAR(20) COMMENT '收货电话',
    receiver_address VARCHAR(500) COMMENT '收货地址',
    delivery_amount DECIMAL(15, 2) COMMENT '本次发货金额',
    approval_status VARCHAR(20) DEFAULT 'pending' COMMENT '审批状态：pending/approved/rejected',
    approval_comment TEXT COMMENT '审批意见',
    approved_by INT UNSIGNED COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    special_approval TINYINT(1) DEFAULT 0 COMMENT '是否特殊审批',
    special_approver_id INT UNSIGNED COMMENT '特殊审批人ID',
    special_approval_reason TEXT COMMENT '特殊审批原因',
    delivery_status VARCHAR(20) DEFAULT 'draft' COMMENT '送货单状态：draft/approved/printed/shipped/received/returned',
    print_date DATETIME COMMENT '打印时间',
    ship_date DATETIME COMMENT '实际发货时间',
    receive_date DATE COMMENT '客户签收日期',
    return_status VARCHAR(20) DEFAULT 'pending' COMMENT '送货单回收状态：pending/received/lost',
    return_date DATE COMMENT '回收日期',
    signed_delivery_file_id INT UNSIGNED COMMENT '签收送货单文件ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_delivery_no (delivery_no),
    INDEX idx_order_delivery (order_id),
    INDEX idx_customer_delivery (customer_id),
    INDEX idx_status_delivery (delivery_status),
    INDEX idx_return_status (return_status),
    FOREIGN KEY (order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (special_approver_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发货单表';

-- ============================================
-- 10. 验收单跟踪表（商务支持角度）
-- ============================================
CREATE TABLE IF NOT EXISTS acceptance_tracking (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    acceptance_order_id INT UNSIGNED NOT NULL COMMENT '验收单ID',
    acceptance_order_no VARCHAR(50) COMMENT '验收单号',
    project_id INT UNSIGNED NOT NULL COMMENT '项目ID',
    project_code VARCHAR(50) COMMENT '项目编号',
    customer_id INT UNSIGNED NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    condition_check_status VARCHAR(20) DEFAULT 'pending' COMMENT '验收条件检查状态：pending/checking/met/not_met',
    condition_check_result TEXT COMMENT '验收条件检查结果',
    condition_check_date DATETIME COMMENT '验收条件检查日期',
    condition_checker_id INT UNSIGNED COMMENT '检查人ID',
    tracking_status VARCHAR(20) DEFAULT 'pending' COMMENT '跟踪状态：pending/reminded/received',
    reminder_count INT DEFAULT 0 COMMENT '催签次数',
    last_reminder_date DATETIME COMMENT '最后催签日期',
    last_reminder_by INT UNSIGNED COMMENT '最后催签人ID',
    received_date DATE COMMENT '收到原件日期',
    signed_file_id INT UNSIGNED COMMENT '签收验收单文件ID',
    report_status VARCHAR(20) DEFAULT 'pending' COMMENT '报告状态：pending/generated/signed/archived',
    report_generated_date DATETIME COMMENT '报告生成日期',
    report_signed_date DATETIME COMMENT '报告签署日期',
    report_archived_date DATETIME COMMENT '报告归档日期',
    warranty_start_date DATE COMMENT '质保开始日期',
    warranty_end_date DATE COMMENT '质保结束日期',
    warranty_status VARCHAR(20) DEFAULT 'not_started' COMMENT '质保状态：not_started/active/expiring/expired',
    warranty_expiry_reminded TINYINT(1) DEFAULT 0 COMMENT '是否已提醒质保到期',
    contract_id INT UNSIGNED COMMENT '合同ID',
    contract_no VARCHAR(50) COMMENT '合同编号',
    sales_person_id INT UNSIGNED COMMENT '业务员ID',
    sales_person_name VARCHAR(50) COMMENT '业务员',
    support_person_id INT UNSIGNED COMMENT '商务支持ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_acceptance_order_tracking (acceptance_order_id),
    INDEX idx_project_tracking (project_id),
    INDEX idx_customer_tracking (customer_id),
    INDEX idx_tracking_status (tracking_status),
    INDEX idx_condition_status (condition_check_status),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
    FOREIGN KEY (condition_checker_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (last_reminder_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (sales_person_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (support_person_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收单跟踪表（商务支持角度）';

-- ============================================
-- 11. 验收单跟踪记录明细表
-- ============================================
CREATE TABLE IF NOT EXISTS acceptance_tracking_records (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    tracking_id INT UNSIGNED NOT NULL COMMENT '跟踪记录ID',
    record_type VARCHAR(20) NOT NULL COMMENT '记录类型：reminder/condition_check/report_track/warranty_reminder',
    record_content TEXT COMMENT '记录内容',
    record_date DATETIME NOT NULL COMMENT '记录日期',
    operator_id INT UNSIGNED NOT NULL COMMENT '操作人ID',
    operator_name VARCHAR(50) COMMENT '操作人',
    result VARCHAR(20) COMMENT '操作结果：success/failed/pending',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_tracking_record (tracking_id),
    INDEX idx_record_type (record_type),
    INDEX idx_record_date (record_date),
    FOREIGN KEY (tracking_id) REFERENCES acceptance_tracking(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收单跟踪记录明细表';

-- ============================================
-- 12. 客户对账单表
-- ============================================
CREATE TABLE IF NOT EXISTS reconciliations (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    reconciliation_no VARCHAR(50) NOT NULL UNIQUE COMMENT '对账单号',
    customer_id INT UNSIGNED NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    period_start DATE COMMENT '对账开始日期',
    period_end DATE COMMENT '对账结束日期',
    opening_balance DECIMAL(15, 2) DEFAULT 0 COMMENT '期初余额',
    period_sales DECIMAL(15, 2) DEFAULT 0 COMMENT '本期销售',
    period_receipt DECIMAL(15, 2) DEFAULT 0 COMMENT '本期回款',
    closing_balance DECIMAL(15, 2) DEFAULT 0 COMMENT '期末余额',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft/sent/confirmed/disputed',
    sent_date DATE COMMENT '发送日期',
    confirm_date DATE COMMENT '确认日期',
    customer_confirmed TINYINT(1) DEFAULT 0 COMMENT '客户是否确认',
    customer_confirm_date DATE COMMENT '客户确认日期',
    customer_difference DECIMAL(15, 2) COMMENT '客户差异金额',
    difference_reason TEXT COMMENT '差异原因',
    reconciliation_file_id INT UNSIGNED COMMENT '对账单文件ID',
    confirmed_file_id INT UNSIGNED COMMENT '确认回执文件ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_reconciliation_no (reconciliation_no),
    INDEX idx_customer_reconciliation (customer_id),
    INDEX idx_period (period_start, period_end),
    INDEX idx_status_reconciliation (status),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户对账单表';

