-- ========================================
-- 项目变更管理模块 - MySQL
-- 创建时间: 2026-02-14
-- 描述: 变更请求、审批记录、通知记录
-- ========================================

-- ==================== 变更请求表 ====================

CREATE TABLE IF NOT EXISTS change_requests (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    change_code VARCHAR(50) NOT NULL UNIQUE COMMENT '变更编号',
    project_id INT NOT NULL COMMENT '项目ID',
    
    -- 变更基本信息
    title VARCHAR(200) NOT NULL COMMENT '变更标题',
    description TEXT COMMENT '变更描述',
    change_type ENUM('REQUIREMENT', 'DESIGN', 'SCOPE', 'TECHNICAL') NOT NULL COMMENT '变更类型',
    change_source ENUM('CUSTOMER', 'INTERNAL') NOT NULL COMMENT '变更来源',
    
    -- 提出人信息
    submitter_id INT NOT NULL COMMENT '提交人ID',
    submitter_name VARCHAR(50) COMMENT '提交人姓名',
    submit_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交日期',
    
    -- 影响评估
    cost_impact DECIMAL(15,2) COMMENT '成本影响（元）',
    cost_impact_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') COMMENT '成本影响程度',
    time_impact INT COMMENT '时间影响（天）',
    time_impact_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') COMMENT '时间影响程度',
    scope_impact TEXT COMMENT '范围影响描述',
    scope_impact_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') COMMENT '范围影响程度',
    risk_assessment TEXT COMMENT '风险评估',
    impact_details JSON COMMENT '影响评估详情',
    
    -- 工作流状态
    status ENUM('SUBMITTED', 'ASSESSING', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 
                'IMPLEMENTING', 'VERIFYING', 'CLOSED', 'CANCELLED') 
           DEFAULT 'SUBMITTED' NOT NULL COMMENT '变更状态',
    
    -- 审批信息
    approver_id INT COMMENT '审批人ID',
    approver_name VARCHAR(50) COMMENT '审批人姓名',
    approval_date DATETIME COMMENT '审批日期',
    approval_decision ENUM('PENDING', 'APPROVED', 'REJECTED', 'RETURNED') 
                     DEFAULT 'PENDING' COMMENT '审批决策',
    approval_comments TEXT COMMENT '审批意见',
    
    -- 实施信息
    implementation_plan TEXT COMMENT '实施计划',
    implementation_start_date DATETIME COMMENT '实施开始日期',
    implementation_end_date DATETIME COMMENT '实施结束日期',
    implementation_status VARCHAR(50) COMMENT '实施状态',
    implementation_notes TEXT COMMENT '实施备注',
    
    -- 验证信息
    verification_notes TEXT COMMENT '验证说明',
    verification_date DATETIME COMMENT '验证日期',
    verified_by_id INT COMMENT '验证人ID',
    verified_by_name VARCHAR(50) COMMENT '验证人姓名',
    
    -- 关闭信息
    close_date DATETIME COMMENT '关闭日期',
    close_notes TEXT COMMENT '关闭说明',
    
    -- 附件信息
    attachments JSON COMMENT '附件列表',
    
    -- 通知设置
    notify_customer BOOLEAN DEFAULT FALSE COMMENT '是否通知客户',
    notify_team BOOLEAN DEFAULT TRUE COMMENT '是否通知团队',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_change_code (change_code),
    INDEX idx_change_project (project_id),
    INDEX idx_change_status (status),
    INDEX idx_change_type (change_type),
    INDEX idx_change_submit_date (submit_date),
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (submitter_id) REFERENCES users(id),
    FOREIGN KEY (approver_id) REFERENCES users(id),
    FOREIGN KEY (verified_by_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目变更请求表';

-- ==================== 变更审批记录表 ====================

CREATE TABLE IF NOT EXISTS change_approval_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    change_request_id INT NOT NULL COMMENT '变更请求ID',
    
    -- 审批人信息
    approver_id INT NOT NULL COMMENT '审批人ID',
    approver_name VARCHAR(50) COMMENT '审批人姓名',
    approver_role VARCHAR(50) COMMENT '审批人角色',
    
    -- 审批信息
    approval_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '审批日期',
    decision ENUM('PENDING', 'APPROVED', 'REJECTED', 'RETURNED') NOT NULL COMMENT '审批决策',
    comments TEXT COMMENT '审批意见',
    
    -- 审批附件
    attachments JSON COMMENT '审批附件',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_approval_change (change_request_id),
    INDEX idx_approval_approver (approver_id),
    INDEX idx_approval_date (approval_date),
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='变更审批记录表';

-- ==================== 变更通知记录表 ====================

CREATE TABLE IF NOT EXISTS change_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    change_request_id INT NOT NULL COMMENT '变更请求ID',
    
    -- 通知信息
    notification_type VARCHAR(50) NOT NULL COMMENT '通知类型',
    recipient_id INT COMMENT '接收人ID',
    recipient_name VARCHAR(50) COMMENT '接收人姓名',
    recipient_email VARCHAR(100) COMMENT '接收人邮箱',
    
    notification_channel VARCHAR(20) COMMENT '通知渠道',
    notification_title VARCHAR(200) COMMENT '通知标题',
    notification_content TEXT COMMENT '通知内容',
    
    sent_at DATETIME COMMENT '发送时间',
    is_sent BOOLEAN DEFAULT FALSE COMMENT '是否已发送',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    read_at DATETIME COMMENT '阅读时间',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_notification_change (change_request_id),
    INDEX idx_notification_recipient (recipient_id),
    INDEX idx_notification_sent (is_sent),
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='变更通知记录表';
