-- ============================================
-- 销售模块审批工作流系统迁移（MySQL）
-- 创建审批工作流配置表和审批历史记录表
-- ============================================

-- 1) 审批工作流配置表
CREATE TABLE IF NOT EXISTS approval_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_type VARCHAR(20) NOT NULL COMMENT '工作流类型：QUOTE/CONTRACT/INVOICE',
    workflow_name VARCHAR(100) NOT NULL COMMENT '工作流名称',
    description TEXT COMMENT '工作流描述',
    routing_rules JSON COMMENT '审批路由规则（JSON）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_approval_workflow_type (workflow_type),
    INDEX idx_approval_workflow_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批工作流配置表';

-- 2) 审批工作流步骤表
CREATE TABLE IF NOT EXISTS approval_workflow_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id INT NOT NULL,
    step_order INT NOT NULL COMMENT '步骤顺序',
    step_name VARCHAR(100) NOT NULL COMMENT '步骤名称',
    approver_role VARCHAR(50) COMMENT '审批角色（如：SALES_MANAGER）',
    approver_id INT COMMENT '指定审批人ID（可选）',
    is_required BOOLEAN DEFAULT TRUE COMMENT '是否必需',
    can_delegate BOOLEAN DEFAULT TRUE COMMENT '是否允许委托',
    can_withdraw BOOLEAN DEFAULT TRUE COMMENT '是否允许撤回（在下一级审批前）',
    due_hours INT COMMENT '审批期限（小时）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_approval_workflow_step_workflow (workflow_id),
    INDEX idx_approval_workflow_step_order (workflow_id, step_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批工作流步骤表';

-- 3) 审批记录表（每个实体的审批实例）
CREATE TABLE IF NOT EXISTS approval_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL COMMENT '实体类型：QUOTE/CONTRACT/INVOICE',
    entity_id INT NOT NULL COMMENT '实体ID',
    workflow_id INT NOT NULL,
    current_step INT DEFAULT 1 COMMENT '当前审批步骤（从1开始）',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '审批状态：PENDING/APPROVED/REJECTED/CANCELLED',
    initiator_id INT NOT NULL COMMENT '发起人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE RESTRICT,
    FOREIGN KEY (initiator_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_approval_record_entity (entity_type, entity_id),
    INDEX idx_approval_record_workflow (workflow_id),
    INDEX idx_approval_record_status (status),
    INDEX idx_approval_record_initiator (initiator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批记录表';

-- 4) 审批历史表（记录每个审批步骤的历史）
CREATE TABLE IF NOT EXISTS approval_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    approval_record_id INT NOT NULL,
    step_order INT NOT NULL COMMENT '步骤顺序',
    approver_id INT NOT NULL COMMENT '审批人ID',
    action VARCHAR(20) NOT NULL COMMENT '审批操作：APPROVE/REJECT/DELEGATE/WITHDRAW',
    comment TEXT COMMENT '审批意见',
    delegate_to_id INT COMMENT '委托给的用户ID',
    action_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (approval_record_id) REFERENCES approval_records(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (delegate_to_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_approval_history_record (approval_record_id),
    INDEX idx_approval_history_step (approval_record_id, step_order),
    INDEX idx_approval_history_approver (approver_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批历史表';
