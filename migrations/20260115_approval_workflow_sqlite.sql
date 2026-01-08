-- ============================================
-- 销售模块审批工作流系统迁移（SQLite）
-- 创建审批工作流配置表和审批历史记录表
-- ============================================

-- 1) 审批工作流配置表
CREATE TABLE IF NOT EXISTS approval_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_type VARCHAR(20) NOT NULL COMMENT '工作流类型：QUOTE/CONTRACT/INVOICE',
    workflow_name VARCHAR(100) NOT NULL COMMENT '工作流名称',
    description TEXT COMMENT '工作流描述',
    routing_rules TEXT COMMENT '审批路由规则（JSON）',
    is_active BOOLEAN DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2) 审批工作流步骤表
CREATE TABLE IF NOT EXISTS approval_workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL COMMENT '步骤顺序',
    step_name VARCHAR(100) NOT NULL COMMENT '步骤名称',
    approver_role VARCHAR(50) COMMENT '审批角色（如：SALES_MANAGER）',
    approver_id INTEGER COMMENT '指定审批人ID（可选）',
    is_required BOOLEAN DEFAULT 1 COMMENT '是否必需',
    can_delegate BOOLEAN DEFAULT 1 COMMENT '是否允许委托',
    can_withdraw BOOLEAN DEFAULT 1 COMMENT '是否允许撤回（在下一级审批前）',
    due_hours INTEGER COMMENT '审批期限（小时）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 3) 审批记录表（每个实体的审批实例）
CREATE TABLE IF NOT EXISTS approval_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(20) NOT NULL COMMENT '实体类型：QUOTE/CONTRACT/INVOICE',
    entity_id INTEGER NOT NULL COMMENT '实体ID',
    workflow_id INTEGER NOT NULL,
    current_step INTEGER DEFAULT 1 COMMENT '当前审批步骤（从1开始）',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '审批状态：PENDING/APPROVED/REJECTED/CANCELLED',
    initiator_id INTEGER NOT NULL COMMENT '发起人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE RESTRICT,
    FOREIGN KEY (initiator_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- 4) 审批历史表（记录每个审批步骤的历史）
CREATE TABLE IF NOT EXISTS approval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_record_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL COMMENT '步骤顺序',
    approver_id INTEGER NOT NULL COMMENT '审批人ID',
    action VARCHAR(20) NOT NULL COMMENT '审批操作：APPROVE/REJECT/DELEGATE/WITHDRAW',
    comment TEXT COMMENT '审批意见',
    delegate_to_id INTEGER COMMENT '委托给的用户ID',
    action_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approval_record_id) REFERENCES approval_records(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (delegate_to_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_approval_workflow_type ON approval_workflows(workflow_type);
CREATE INDEX IF NOT EXISTS idx_approval_workflow_active ON approval_workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_approval_workflow_step_workflow ON approval_workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflow_step_order ON approval_workflow_steps(workflow_id, step_order);

CREATE INDEX IF NOT EXISTS idx_approval_record_entity ON approval_records(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_record_workflow ON approval_records(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_record_status ON approval_records(status);
CREATE INDEX IF NOT EXISTS idx_approval_record_initiator ON approval_records(initiator_id);

CREATE INDEX IF NOT EXISTS idx_approval_history_record ON approval_history(approval_record_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_step ON approval_history(approval_record_id, step_order);
CREATE INDEX IF NOT EXISTS idx_approval_history_approver ON approval_history(approver_id);
