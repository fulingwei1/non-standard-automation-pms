-- 统一审批系统迁移脚本 (SQLite)
-- 创建日期: 2026-01-20
-- 描述: 创建统一审批系统所需的所有表

-- ============================================================
-- 1. 审批模板表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    category VARCHAR(30);
    description TEXT,
    icon VARCHAR(100),
    form_schema JSON;
    version INTEGER DEFAULT 1,
    is_published INTEGER DEFAULT 0,
    visible_scope JSON;
    entity_type VARCHAR(50);
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_template_code ON approval_templates(template_code);
CREATE INDEX idx_template_category ON approval_templates(category);
CREATE INDEX idx_template_active ON approval_templates(is_active);

-- ============================================================
-- 2. 审批模板版本表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_template_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    form_schema JSON,
    published_by INTEGER,
    published_at DATETIME,
    change_log TEXT,
    snapshot JSON;
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES approval_templates(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);

CREATE INDEX idx_template_version_template ON approval_template_versions(template_id);
CREATE UNIQUE INDEX idx_template_version_unique ON approval_template_versions(template_id, version);

-- ============================================================
-- 3. 审批流程定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_flow_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    flow_name VARCHAR(100) NOT NULL,
    flow_description TEXT,
    is_default INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES approval_templates(id)
);

CREATE INDEX idx_flow_template ON approval_flow_definitions(template_id);
CREATE INDEX idx_flow_active ON approval_flow_definitions(is_active);
CREATE INDEX idx_flow_default ON approval_flow_definitions(template_id, is_default);

-- ============================================================
-- 4. 审批节点定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_node_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL,
    node_code VARCHAR(50),
    node_name VARCHAR(100) NOT NULL,
    node_order INTEGER DEFAULT 0,
    node_type VARCHAR(20) DEFAULT 'APPROVAL';
    approval_mode VARCHAR(20) DEFAULT 'SINGLE';
    approver_type VARCHAR(20);
    approver_config JSON;
    condition_expression TEXT;
    can_add_approver INTEGER DEFAULT 0,
    can_transfer INTEGER DEFAULT 1,
    can_delegate INTEGER DEFAULT 1,
    can_reject_to VARCHAR(20) DEFAULT 'START';
    reject_to_node_id INTEGER;
    timeout_hours INTEGER,
    timeout_action VARCHAR(20);
    timeout_notify_config JSON;
    notify_config JSON;
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flow_id) REFERENCES approval_flow_definitions(id),
    FOREIGN KEY (reject_to_node_id) REFERENCES approval_node_definitions(id)
);

CREATE INDEX idx_node_flow ON approval_node_definitions(flow_id);
CREATE INDEX idx_node_order ON approval_node_definitions(flow_id, node_order);
CREATE INDEX idx_node_type ON approval_node_definitions(node_type);

-- ============================================================
-- 5. 审批路由规则表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_routing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    flow_id INTEGER NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    rule_order INTEGER DEFAULT 0,
    conditions JSON;
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES approval_templates(id),
    FOREIGN KEY (flow_id) REFERENCES approval_flow_definitions(id)
);

CREATE INDEX idx_routing_template ON approval_routing_rules(template_id);
CREATE INDEX idx_routing_order ON approval_routing_rules(template_id, rule_order);

-- ============================================================
-- 6. 审批实例表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_no VARCHAR(50) UNIQUE NOT NULL,
    template_id INTEGER NOT NULL,
    flow_id INTEGER,
    entity_type VARCHAR(50);
    entity_id INTEGER;
    initiator_id INTEGER NOT NULL,
    initiator_name VARCHAR(50),
    initiator_dept_id INTEGER,
    form_data JSON,
    status VARCHAR(20) DEFAULT 'DRAFT';
    current_node_id INTEGER,
    urgency VARCHAR(10) DEFAULT 'NORMAL';
    title VARCHAR(200),
    summary TEXT,
    submitted_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES approval_templates(id),
    FOREIGN KEY (flow_id) REFERENCES approval_flow_definitions(id),
    FOREIGN KEY (initiator_id) REFERENCES users(id),
    FOREIGN KEY (initiator_dept_id) REFERENCES departments(id),
    FOREIGN KEY (current_node_id) REFERENCES approval_node_definitions(id)
);

CREATE INDEX idx_instance_no ON approval_instances(instance_no);
CREATE INDEX idx_instance_template ON approval_instances(template_id);
CREATE INDEX idx_instance_entity ON approval_instances(entity_type, entity_id);
CREATE INDEX idx_instance_initiator ON approval_instances(initiator_id);
CREATE INDEX idx_instance_status ON approval_instances(status);
CREATE INDEX idx_instance_submitted ON approval_instances(submitted_at);
CREATE INDEX idx_instance_initiator_status ON approval_instances(initiator_id, status);

-- ============================================================
-- 7. 审批任务表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    task_type VARCHAR(20) DEFAULT 'APPROVAL';
    task_order INTEGER DEFAULT 1,
    assignee_id INTEGER NOT NULL,
    assignee_name VARCHAR(50),
    assignee_dept_id INTEGER,
    assignee_type VARCHAR(20) DEFAULT 'NORMAL';
    original_assignee_id INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING';
    action VARCHAR(20);
    comment TEXT,
    attachments JSON,
    eval_data JSON;
    return_to_node_id INTEGER,
    due_at DATETIME,
    reminded_at DATETIME,
    remind_count INTEGER DEFAULT 0,
    completed_at DATETIME,
    is_countersign INTEGER DEFAULT 0,
    countersign_weight INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (node_id) REFERENCES approval_node_definitions(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (assignee_dept_id) REFERENCES departments(id),
    FOREIGN KEY (original_assignee_id) REFERENCES users(id),
    FOREIGN KEY (return_to_node_id) REFERENCES approval_node_definitions(id)
);

CREATE INDEX idx_task_instance ON approval_tasks(instance_id);
CREATE INDEX idx_task_node ON approval_tasks(node_id);
CREATE INDEX idx_task_assignee ON approval_tasks(assignee_id);
CREATE INDEX idx_task_status ON approval_tasks(status);
CREATE INDEX idx_task_pending ON approval_tasks(assignee_id, status);
CREATE INDEX idx_task_due ON approval_tasks(due_at);
CREATE INDEX idx_task_type ON approval_tasks(task_type);

-- ============================================================
-- 8. 抄送记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_carbon_copies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    node_id INTEGER,
    cc_user_id INTEGER NOT NULL,
    cc_user_name VARCHAR(50),
    cc_source VARCHAR(20) DEFAULT 'FLOW';
    added_by INTEGER,
    is_read INTEGER DEFAULT 0,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (cc_user_id) REFERENCES users(id),
    FOREIGN KEY (added_by) REFERENCES users(id)
);

CREATE INDEX idx_cc_instance ON approval_carbon_copies(instance_id);
CREATE INDEX idx_cc_user ON approval_carbon_copies(cc_user_id);
CREATE INDEX idx_cc_unread ON approval_carbon_copies(cc_user_id, is_read);

-- ============================================================
-- 9. 会签结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_countersign_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    total_count INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    final_result VARCHAR(20);
    result_reason TEXT,
    summary_data JSON;
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (node_id) REFERENCES approval_node_definitions(id)
);

CREATE INDEX idx_countersign_instance ON approval_countersign_results(instance_id);
CREATE INDEX idx_countersign_node ON approval_countersign_results(node_id);
CREATE UNIQUE INDEX idx_countersign_instance_node ON approval_countersign_results(instance_id, node_id);

-- ============================================================
-- 10. 审批操作日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    task_id INTEGER,
    node_id INTEGER,
    operator_id INTEGER NOT NULL,
    operator_name VARCHAR(50),
    action VARCHAR(30) NOT NULL;
    action_detail JSON,
    comment TEXT,
    attachments JSON,
    before_status VARCHAR(20),
    after_status VARCHAR(20),
    before_node_id INTEGER,
    after_node_id INTEGER,
    action_at DATETIME NOT NULL,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (task_id) REFERENCES approval_tasks(id),
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX idx_action_log_instance ON approval_action_logs(instance_id);
CREATE INDEX idx_action_log_task ON approval_action_logs(task_id);
CREATE INDEX idx_action_log_operator ON approval_action_logs(operator_id);
CREATE INDEX idx_action_log_action ON approval_action_logs(action);
CREATE INDEX idx_action_log_time ON approval_action_logs(action_at);
CREATE INDEX idx_action_log_instance_time ON approval_action_logs(instance_id, action_at);

-- ============================================================
-- 11. 审批评论表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(50),
    content TEXT NOT NULL,
    attachments JSON,
    parent_id INTEGER,
    reply_to_user_id INTEGER,
    mentioned_user_ids JSON,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME,
    deleted_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES approval_comments(id),
    FOREIGN KEY (reply_to_user_id) REFERENCES users(id),
    FOREIGN KEY (deleted_by) REFERENCES users(id)
);

CREATE INDEX idx_comment_instance ON approval_comments(instance_id);
CREATE INDEX idx_comment_user ON approval_comments(user_id);
CREATE INDEX idx_comment_parent ON approval_comments(parent_id);

-- ============================================================
-- 12. 审批代理人配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_delegates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL;
    delegate_id INTEGER NOT NULL;
    scope VARCHAR(20) DEFAULT 'ALL';
    template_ids JSON;
    categories JSON;
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active INTEGER DEFAULT 1,
    reason VARCHAR(200),
    notify_original INTEGER DEFAULT 1,
    notify_delegate INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (delegate_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_delegate_user ON approval_delegates(user_id);
CREATE INDEX idx_delegate_delegate ON approval_delegates(delegate_id);
CREATE INDEX idx_delegate_active ON approval_delegates(is_active);
CREATE INDEX idx_delegate_date_range ON approval_delegates(start_date, end_date);
CREATE INDEX idx_delegate_user_active ON approval_delegates(user_id, is_active);

-- ============================================================
-- 13. 代理审批日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_delegate_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delegate_config_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    instance_id INTEGER NOT NULL,
    original_user_id INTEGER NOT NULL,
    delegate_user_id INTEGER NOT NULL,
    action VARCHAR(20),
    action_at DATETIME,
    original_notified INTEGER DEFAULT 0,
    original_notified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (delegate_config_id) REFERENCES approval_delegates(id),
    FOREIGN KEY (task_id) REFERENCES approval_tasks(id),
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (original_user_id) REFERENCES users(id),
    FOREIGN KEY (delegate_user_id) REFERENCES users(id)
);

CREATE INDEX idx_delegate_log_config ON approval_delegate_logs(delegate_config_id);
CREATE INDEX idx_delegate_log_task ON approval_delegate_logs(task_id);
CREATE INDEX idx_delegate_log_original ON approval_delegate_logs(original_user_id);

-- ============================================================
-- 插入默认审批模板
-- ============================================================

-- 报价审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('QUOTE_APPROVAL', '报价审批', 'BUSINESS', '报价单审批流程，根据毛利率自动选择审批层级', 'QUOTE', 1, 1);

-- 合同审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('CONTRACT_APPROVAL', '合同审批', 'BUSINESS', '销售合同审批流程', 'CONTRACT', 1, 1);

-- 发票审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('INVOICE_APPROVAL', '发票审批', 'FINANCE', '开票申请审批流程', 'INVOICE', 1, 1);

-- ECN审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('ECN_APPROVAL', 'ECN审批', 'ENGINEERING', '工程变更通知审批流程，支持多部门会签评估', 'ECN', 1, 1);

-- 项目审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('PROJECT_APPROVAL', '项目审批', 'PROJECT', '项目立项审批流程', 'PROJECT', 1, 1);

-- 请假审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active,
    form_schema)
VALUES ('LEAVE_REQUEST', '请假申请', 'HR', '员工请假审批流程，根据请假天数自动选择审批层级', 'LEAVE', 1, 1,
    '{"fields":[{"name":"leave_type","type":"select","label":"请假类型","options":["年假","事假","病假","婚假","产假","丧假"],"required":true},{"name":"start_date","type":"date","label":"开始日期","required":true},{"name":"end_date","type":"date","label":"结束日期","required":true},{"name":"leave_days","type":"number","label":"请假天数","required":true},{"name":"reason","type":"textarea","label":"请假原因","required":true}]}');

-- 采购审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('PURCHASE_APPROVAL', '采购审批', 'FINANCE', '采购申请审批流程，根据金额自动选择审批层级', 'PURCHASE', 1, 1);

-- 工时审批模板
INSERT INTO approval_templates (template_code, template_name, category, description, entity_type, is_published, is_active)
VALUES ('TIMESHEET_APPROVAL', '工时审批', 'HR', '员工工时审批流程', 'TIMESHEET', 1, 1);

COMMIT;
