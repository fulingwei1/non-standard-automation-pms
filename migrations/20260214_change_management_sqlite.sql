-- ========================================
-- 项目变更管理模块 - SQLite
-- 创建时间: 2026-02-14
-- 描述: 变更请求、审批记录、通知记录
-- ========================================

-- ==================== 变更请求表 ====================

CREATE TABLE IF NOT EXISTS change_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_code VARCHAR(50) NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,
    
    -- 变更基本信息
    title VARCHAR(200) NOT NULL,
    description TEXT,
    change_type VARCHAR(20) NOT NULL,  -- REQUIREMENT/DESIGN/SCOPE/TECHNICAL
    change_source VARCHAR(20) NOT NULL,  -- CUSTOMER/INTERNAL
    
    -- 提出人信息
    submitter_id INTEGER NOT NULL,
    submitter_name VARCHAR(50),
    submit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 影响评估
    cost_impact DECIMAL(15,2),
    cost_impact_level VARCHAR(20),  -- LOW/MEDIUM/HIGH/CRITICAL
    time_impact INTEGER,  -- 天数
    time_impact_level VARCHAR(20),  -- LOW/MEDIUM/HIGH/CRITICAL
    scope_impact TEXT,
    scope_impact_level VARCHAR(20),  -- LOW/MEDIUM/HIGH/CRITICAL
    risk_assessment TEXT,
    impact_details TEXT,  -- JSON格式
    
    -- 工作流状态
    status VARCHAR(20) DEFAULT 'SUBMITTED' NOT NULL,  
    -- SUBMITTED/ASSESSING/PENDING_APPROVAL/APPROVED/REJECTED/
    -- IMPLEMENTING/VERIFYING/CLOSED/CANCELLED
    
    -- 审批信息
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_date DATETIME,
    approval_decision VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/APPROVED/REJECTED/RETURNED
    approval_comments TEXT,
    
    -- 实施信息
    implementation_plan TEXT,
    implementation_start_date DATETIME,
    implementation_end_date DATETIME,
    implementation_status VARCHAR(50),
    implementation_notes TEXT,
    
    -- 验证信息
    verification_notes TEXT,
    verification_date DATETIME,
    verified_by_id INTEGER,
    verified_by_name VARCHAR(50),
    
    -- 关闭信息
    close_date DATETIME,
    close_notes TEXT,
    
    -- 附件信息
    attachments TEXT,  -- JSON数组
    
    -- 通知设置
    notify_customer BOOLEAN DEFAULT 0,
    notify_team BOOLEAN DEFAULT 1,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (submitter_id) REFERENCES users(id),
    FOREIGN KEY (approver_id) REFERENCES users(id),
    FOREIGN KEY (verified_by_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_change_code ON change_requests(change_code);
CREATE INDEX idx_change_project ON change_requests(project_id);
CREATE INDEX idx_change_status ON change_requests(status);
CREATE INDEX idx_change_type ON change_requests(change_type);
CREATE INDEX idx_change_submit_date ON change_requests(submit_date);

-- ==================== 变更审批记录表 ====================

CREATE TABLE IF NOT EXISTS change_approval_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    
    -- 审批人信息
    approver_id INTEGER NOT NULL,
    approver_name VARCHAR(50),
    approver_role VARCHAR(50),
    
    -- 审批信息
    approval_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    decision VARCHAR(20) NOT NULL,  -- PENDING/APPROVED/REJECTED/RETURNED
    comments TEXT,
    
    -- 审批附件
    attachments TEXT,  -- JSON数组
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_approval_change ON change_approval_records(change_request_id);
CREATE INDEX idx_approval_approver ON change_approval_records(approver_id);
CREATE INDEX idx_approval_date ON change_approval_records(approval_date);

-- ==================== 变更通知记录表 ====================

CREATE TABLE IF NOT EXISTS change_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    
    -- 通知信息
    notification_type VARCHAR(50) NOT NULL,  -- SUBMITTED/APPROVED/REJECTED/IMPLEMENTING/COMPLETED
    recipient_id INTEGER,
    recipient_name VARCHAR(50),
    recipient_email VARCHAR(100),
    
    notification_channel VARCHAR(20),  -- EMAIL/SMS/SYSTEM
    notification_title VARCHAR(200),
    notification_content TEXT,
    
    sent_at DATETIME,
    is_sent BOOLEAN DEFAULT 0,
    is_read BOOLEAN DEFAULT 0,
    read_at DATETIME,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_notification_change ON change_notifications(change_request_id);
CREATE INDEX idx_notification_recipient ON change_notifications(recipient_id);
CREATE INDEX idx_notification_sent ON change_notifications(is_sent);

-- ==================== 更新触发器 ====================

-- change_requests 更新时间触发器
CREATE TRIGGER IF NOT EXISTS update_change_requests_timestamp 
AFTER UPDATE ON change_requests
FOR EACH ROW
BEGIN
    UPDATE change_requests SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- change_approval_records 更新时间触发器
CREATE TRIGGER IF NOT EXISTS update_change_approval_records_timestamp 
AFTER UPDATE ON change_approval_records
FOR EACH ROW
BEGIN
    UPDATE change_approval_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- change_notifications 更新时间触发器
CREATE TRIGGER IF NOT EXISTS update_change_notifications_timestamp 
AFTER UPDATE ON change_notifications
FOR EACH ROW
BEGIN
    UPDATE change_notifications SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
