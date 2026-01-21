-- 统一审批系统迁移脚本 (SQLite) - 修复版
-- 创建日期: 2026-01-21
-- 描述: 创建统一审批系统所需的所有表（修复SQLite语法兼容性）

-- ============================================================
-- 1. 审批模板表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    category VARCHAR(30),                          -- 分类：HR/FINANCE/PROJECT/BUSINESS/ENGINEERING
    description TEXT,
    icon VARCHAR(100),
    entity_type VARCHAR(50),                       -- 关联的业务实体类型
    form_schema JSON,                              -- 表单结构定义（JSON Schema）
    version INTEGER DEFAULT 1,
    is_published INTEGER DEFAULT 0,
    published_at DATETIME,
    published_by INTEGER REFERENCES users(id),
    visible_scope JSON,                            -- 可见范围（部门/角色ID列表）
    is_active INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_template_code ON approval_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_approval_template_category ON approval_templates(category);
CREATE INDEX IF NOT EXISTS idx_approval_template_entity_type ON approval_templates(entity_type);
CREATE INDEX IF NOT EXISTS idx_approval_template_active ON approval_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_approval_template_published ON approval_templates(is_published);

-- ============================================================
-- 2. 审批模板版本表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_template_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES approval_templates(id),
    version INTEGER NOT NULL,
    template_name VARCHAR(100),
    form_schema JSON,
    flow_snapshot JSON,                            -- 流程定义快照
    change_log TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_version_template ON approval_template_versions(template_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_template_version_version ON approval_template_versions(template_id, version);

-- ============================================================
-- 3. 审批流程定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_flow_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES approval_templates(id),
    flow_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default INTEGER DEFAULT 0,                  -- 是否为默认流程
    version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_flow_template ON approval_flow_definitions(template_id);
CREATE INDEX IF NOT EXISTS idx_approval_flow_active ON approval_flow_definitions(is_active);
CREATE INDEX IF NOT EXISTS idx_approval_flow_default ON approval_flow_definitions(template_id, is_default);

-- ============================================================
-- 4. 审批节点定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_node_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES approval_flow_definitions(id),
    node_code VARCHAR(50),
    node_name VARCHAR(100) NOT NULL,
    node_order INTEGER NOT NULL,
    -- 节点类型: APPROVAL/CC/CONDITION/PARALLEL/JOIN
    node_type VARCHAR(20) NOT NULL DEFAULT 'APPROVAL',
    -- 审批模式: SINGLE/OR_SIGN/AND_SIGN/SEQUENTIAL
    approval_mode VARCHAR(20) DEFAULT 'SINGLE',
    -- 审批人确定方式: FIXED_USER/ROLE/DEPARTMENT_HEAD/DIRECT_MANAGER/FORM_FIELD/INITIATOR_DEPT_HEAD/MULTI_DEPT/DYNAMIC
    approver_type VARCHAR(30),
    approver_config JSON,                          -- 审批人配置详情
    condition_expression TEXT,                     -- 条件表达式（CONDITION类型）
    branches JSON,                                 -- 分支配置
    can_add_approver INTEGER DEFAULT 0,
    can_transfer INTEGER DEFAULT 1,
    can_delegate INTEGER DEFAULT 1,
    -- 驳回目标: START/PREV/SPECIFIC/NONE
    can_reject_to VARCHAR(20) DEFAULT 'START',
    timeout_hours INTEGER,
    -- 超时操作: REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE
    timeout_action VARCHAR(20),
    timeout_remind_hours INTEGER,
    notify_config JSON,                            -- 通知配置
    eval_form_schema JSON,                         -- 评估表单定义
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_node_flow ON approval_node_definitions(flow_id);
CREATE INDEX IF NOT EXISTS idx_approval_node_order ON approval_node_definitions(flow_id, node_order);
CREATE INDEX IF NOT EXISTS idx_approval_node_type ON approval_node_definitions(node_type);

-- ============================================================
-- 5. 审批路由规则表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_routing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES approval_templates(id),
    flow_id INTEGER NOT NULL REFERENCES approval_flow_definitions(id),
    rule_name VARCHAR(100) NOT NULL,
    rule_order INTEGER NOT NULL,                   -- 规则优先级（数字越小优先级越高）
    description TEXT,
    conditions JSON NOT NULL,                      -- 条件配置JSON
    is_active INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_routing_rule_template ON approval_routing_rules(template_id);
CREATE INDEX IF NOT EXISTS idx_routing_rule_order ON approval_routing_rules(template_id, rule_order);
CREATE INDEX IF NOT EXISTS idx_routing_rule_active ON approval_routing_rules(is_active);

-- ============================================================
-- 6. 审批实例表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_no VARCHAR(50) UNIQUE NOT NULL,
    template_id INTEGER NOT NULL REFERENCES approval_templates(id),
    flow_id INTEGER REFERENCES approval_flow_definitions(id),
    -- 多态关联
    entity_type VARCHAR(50),                       -- 业务实体类型
    entity_id INTEGER,                             -- 业务实体ID
    -- 发起人信息
    initiator_id INTEGER NOT NULL REFERENCES users(id),
    initiator_dept_id INTEGER REFERENCES departments(id),
    -- 表单数据
    form_data JSON,
    -- 状态: DRAFT/PENDING/APPROVED/REJECTED/CANCELLED/TERMINATED
    status VARCHAR(20) DEFAULT 'PENDING',
    current_node_id INTEGER REFERENCES approval_node_definitions(id),
    current_node_order INTEGER,
    -- 紧急程度: NORMAL/URGENT/CRITICAL
    urgency VARCHAR(10) DEFAULT 'NORMAL',
    title VARCHAR(200),
    summary TEXT,
    submitted_at DATETIME,
    completed_at DATETIME,
    final_comment TEXT,
    final_approver_id INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_instance_no ON approval_instances(instance_no);
CREATE INDEX IF NOT EXISTS idx_approval_instance_template ON approval_instances(template_id);
CREATE INDEX IF NOT EXISTS idx_approval_instance_entity ON approval_instances(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_instance_initiator ON approval_instances(initiator_id);
CREATE INDEX IF NOT EXISTS idx_approval_instance_status ON approval_instances(status);
CREATE INDEX IF NOT EXISTS idx_approval_instance_urgency ON approval_instances(urgency);
CREATE INDEX IF NOT EXISTS idx_approval_instance_submitted ON approval_instances(submitted_at);
CREATE INDEX IF NOT EXISTS idx_approval_instance_current_node ON approval_instances(current_node_id);

-- ============================================================
-- 7. 审批任务表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    node_id INTEGER NOT NULL REFERENCES approval_node_definitions(id),
    -- 任务类型: APPROVAL/CC/EVALUATION
    task_type VARCHAR(20) DEFAULT 'APPROVAL',
    task_order INTEGER DEFAULT 1,
    -- 审批人信息
    assignee_id INTEGER NOT NULL REFERENCES users(id),
    assignee_name VARCHAR(50),
    assignee_dept_id INTEGER REFERENCES departments(id),
    -- 分配类型: NORMAL/DELEGATED/TRANSFERRED/ADDED_BEFORE/ADDED_AFTER
    assignee_type VARCHAR(20) DEFAULT 'NORMAL',
    original_assignee_id INTEGER REFERENCES users(id),
    -- 任务状态: PENDING/COMPLETED/TRANSFERRED/DELEGATED/SKIPPED/EXPIRED/CANCELLED
    status VARCHAR(20) DEFAULT 'PENDING',
    -- 审批操作: APPROVE/REJECT/RETURN
    action VARCHAR(20),
    comment TEXT,
    attachments JSON,
    eval_data JSON,                                -- 评估数据（ECN等场景）
    return_to_node_id INTEGER REFERENCES approval_node_definitions(id),
    due_at DATETIME,
    reminded_at DATETIME,
    remind_count INTEGER DEFAULT 0,
    completed_at DATETIME,
    is_countersign INTEGER DEFAULT 0,
    countersign_weight INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_task_instance ON approval_tasks(instance_id);
CREATE INDEX IF NOT EXISTS idx_approval_task_node ON approval_tasks(node_id);
CREATE INDEX IF NOT EXISTS idx_approval_task_assignee ON approval_tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_approval_task_status ON approval_tasks(status);
CREATE INDEX IF NOT EXISTS idx_approval_task_pending ON approval_tasks(assignee_id, status);
CREATE INDEX IF NOT EXISTS idx_approval_task_due ON approval_tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_approval_task_type ON approval_tasks(task_type);

-- ============================================================
-- 8. 抄送记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_carbon_copies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    node_id INTEGER,
    cc_user_id INTEGER NOT NULL REFERENCES users(id),
    cc_user_name VARCHAR(50),
    -- 抄送来源: FLOW/INITIATOR/APPROVER
    cc_source VARCHAR(20) DEFAULT 'FLOW',
    added_by INTEGER REFERENCES users(id),
    is_read INTEGER DEFAULT 0,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_cc_instance ON approval_carbon_copies(instance_id);
CREATE INDEX IF NOT EXISTS idx_approval_cc_user ON approval_carbon_copies(cc_user_id);
CREATE INDEX IF NOT EXISTS idx_approval_cc_unread ON approval_carbon_copies(cc_user_id, is_read);

-- ============================================================
-- 9. 会签结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_countersign_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    node_id INTEGER NOT NULL REFERENCES approval_node_definitions(id),
    total_count INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    -- 最终结果: PENDING/PASSED/FAILED
    final_result VARCHAR(20),
    result_reason TEXT,
    summary_data JSON,                             -- 汇总数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_countersign_instance ON approval_countersign_results(instance_id);
CREATE INDEX IF NOT EXISTS idx_countersign_node ON approval_countersign_results(node_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_countersign_instance_node ON approval_countersign_results(instance_id, node_id);

-- ============================================================
-- 10. 审批操作日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    task_id INTEGER REFERENCES approval_tasks(id),
    node_id INTEGER REFERENCES approval_node_definitions(id),
    operator_id INTEGER NOT NULL REFERENCES users(id),
    operator_name VARCHAR(50),
    -- 操作类型: SUBMIT/SAVE_DRAFT/APPROVE/REJECT/RETURN/TRANSFER/DELEGATE/ADD_APPROVER_BEFORE/ADD_APPROVER_AFTER/ADD_CC/WITHDRAW/CANCEL/TERMINATE/REMIND/COMMENT/READ_CC/TIMEOUT
    action VARCHAR(30) NOT NULL,
    action_detail JSON,
    comment TEXT,
    attachments JSON,
    before_status VARCHAR(20),
    after_status VARCHAR(20),
    before_node_id INTEGER,
    after_node_id INTEGER,
    action_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_action_log_instance ON approval_action_logs(instance_id);
CREATE INDEX IF NOT EXISTS idx_action_log_task ON approval_action_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_action_log_operator ON approval_action_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_action_log_action ON approval_action_logs(action);
CREATE INDEX IF NOT EXISTS idx_action_log_time ON approval_action_logs(action_at);
CREATE INDEX IF NOT EXISTS idx_action_log_instance_time ON approval_action_logs(instance_id, action_at);

-- ============================================================
-- 11. 审批评论表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    user_name VARCHAR(50),
    content TEXT NOT NULL,
    attachments JSON,
    parent_id INTEGER REFERENCES approval_comments(id),
    reply_to_user_id INTEGER REFERENCES users(id),
    mentioned_user_ids JSON,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME,
    deleted_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_comment_instance ON approval_comments(instance_id);
CREATE INDEX IF NOT EXISTS idx_comment_user ON approval_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comment_parent ON approval_comments(parent_id);

-- ============================================================
-- 12. 审批代理人配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_delegates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),           -- 原审批人ID
    delegate_id INTEGER NOT NULL REFERENCES users(id),       -- 代理人ID
    -- 代理范围: ALL/TEMPLATE/CATEGORY
    scope VARCHAR(20) DEFAULT 'ALL',
    template_ids JSON,                             -- 指定模板ID列表
    categories JSON,                               -- 指定分类列表
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active INTEGER DEFAULT 1,
    reason VARCHAR(200),
    notify_original INTEGER DEFAULT 1,
    notify_delegate INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delegate_user ON approval_delegates(user_id);
CREATE INDEX IF NOT EXISTS idx_delegate_delegate ON approval_delegates(delegate_id);
CREATE INDEX IF NOT EXISTS idx_delegate_active ON approval_delegates(is_active);
CREATE INDEX IF NOT EXISTS idx_delegate_date_range ON approval_delegates(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_delegate_user_active ON approval_delegates(user_id, is_active);

-- ============================================================
-- 13. 代理审批日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_delegate_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delegate_config_id INTEGER NOT NULL REFERENCES approval_delegates(id),
    task_id INTEGER NOT NULL REFERENCES approval_tasks(id),
    instance_id INTEGER NOT NULL REFERENCES approval_instances(id),
    original_user_id INTEGER NOT NULL REFERENCES users(id),
    delegate_user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(20),                            -- 代理审批的操作
    action_at DATETIME,
    original_notified INTEGER DEFAULT 0,
    original_notified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delegate_log_config ON approval_delegate_logs(delegate_config_id);
CREATE INDEX IF NOT EXISTS idx_delegate_log_task ON approval_delegate_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_delegate_log_original ON approval_delegate_logs(original_user_id);

-- ============================================================
-- 插入默认审批模板
-- ============================================================

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('QUOTE_APPROVAL', '报价审批', 'BUSINESS', '报价单审批流程，根据毛利率自动选择审批层级', 'QUOTE', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('CONTRACT_APPROVAL', '合同审批', 'BUSINESS', '销售合同审批流程', 'CONTRACT', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('INVOICE_APPROVAL', '发票审批', 'FINANCE', '开票申请审批流程', 'INVOICE', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('ECN_APPROVAL', 'ECN审批', 'ENGINEERING', '工程变更通知审批流程，支持多部门会签评估', 'ECN', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('PROJECT_APPROVAL', '项目审批', 'PROJECT', '项目立项审批流程', 'PROJECT', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active, form_schema)
VALUES ('LEAVE_REQUEST', '请假申请', 'HR', '员工请假审批流程，根据请假天数自动选择审批层级', 'LEAVE', 1, 1,
    '{"fields":[{"name":"leave_type","type":"select","label":"请假类型","options":["年假","事假","病假","婚假","产假","丧假"],"required":true},{"name":"start_date","type":"date","label":"开始日期","required":true},{"name":"end_date","type":"date","label":"结束日期","required":true},{"name":"leave_days","type":"number","label":"请假天数","required":true},{"name":"reason","type":"textarea","label":"请假原因","required":true}]}');

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('PURCHASE_APPROVAL', '采购审批', 'FINANCE', '采购申请审批流程，根据金额自动选择审批层级', 'PURCHASE', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('TIMESHEET_APPROVAL', '工时审批', 'HR', '员工工时审批流程', 'TIMESHEET', 1, 1);

INSERT OR IGNORE INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('TASK_APPROVAL', '任务审批', 'PROJECT', '任务审批流程', 'TASK', 1, 1);
