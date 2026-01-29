-- 审批模板补充迁移
-- 创建日期: 2026-01-25
-- 描述:
--   1. 清理无流程定义的旧模板
--   2. 补充节点的 approver_config 字段
--   3. 为 ECN_TEMPLATE 和 PROJECT_TEMPLATE 添加路由规则

-- ============================================================
-- 第一部分: 清理旧模板
-- ============================================================

-- 删除没有流程定义的 LEAVE_REQUEST 模板
DELETE FROM approval_templates
WHERE template_code = 'LEAVE_REQUEST'
AND id NOT IN (SELECT DISTINCT template_id FROM approval_flow_definitions);

-- ============================================================
-- 第二部分: 补充节点配置
-- ============================================================

-- 更新 QUOTE_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["SALES_MANAGER"]}'
WHERE node_code = 'SALES_MGR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'QUOTE_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["SALES_DIRECTOR"]}'
WHERE node_code = 'SALES_DIRECTOR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'QUOTE_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["GENERAL_MANAGER"]}'
WHERE node_code = 'GM_APPROVAL' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'QUOTE_TEMPLATE')
);

-- 更新 CONTRACT_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["SALES_MANAGER"]}'
WHERE node_code = 'SALES_MGR_CONTRACT' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'CONTRACT_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["SALES_DIRECTOR"]}'
WHERE node_code = 'SALES_DIRECTOR_CONTRACT' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'CONTRACT_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["GENERAL_MANAGER"]}'
WHERE node_code = 'GM_CONTRACT' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'CONTRACT_TEMPLATE')
);

-- 更新 INVOICE_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["FINANCE_MANAGER"]}'
WHERE node_code = 'FINANCE_MGR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'INVOICE_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["FINANCE_DIRECTOR"]}'
WHERE node_code = 'FINANCE_DIRECTOR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'INVOICE_TEMPLATE')
);

-- 更新 PURCHASE_REQUEST_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["PURCHASE_MANAGER"]}'
WHERE node_code = 'PURCHASE_MGR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PURCHASE_REQUEST_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["DEPARTMENT_HEAD"]}'
WHERE node_code = 'DEPT_HEAD_PURCHASE' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PURCHASE_REQUEST_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["GENERAL_MANAGER"]}'
WHERE node_code = 'GM_PURCHASE' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PURCHASE_REQUEST_TEMPLATE')
);

-- 更新 LEAVE_REQUEST_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"level": 1}'
WHERE node_code = 'TEAM_LEADER' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'LEAVE_REQUEST_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["DEPARTMENT_HEAD"]}'
WHERE node_code = 'DEPT_HEAD_LEAVE' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'LEAVE_REQUEST_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["HR_MANAGER"]}'
WHERE node_code = 'HR_LEAVE' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'LEAVE_REQUEST_TEMPLATE')
);

-- 更新 PROJECT_TEMPLATE 节点的 approver_config
UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["PROJECT_MANAGER"]}'
WHERE node_code = 'PROJECT_MGR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PROJECT_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["PMO_OFFICER"]}'
WHERE node_code = 'PMO_REVIEW' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PROJECT_TEMPLATE')
);

UPDATE approval_node_definitions
SET approver_config = '{"role_codes": ["DEPARTMENT_DIRECTOR"]}'
WHERE node_code = 'DEPT_DIRECTOR' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'PROJECT_TEMPLATE')
);

-- ============================================================
-- 第三部分: 为 ECN_TEMPLATE 添加路由规则
-- ============================================================

-- ECN 不需要路由规则,所有请求都走标准流程
-- 但为了完整性,可以添加一个默认路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '默认流程', 1, '所有ECN请求都走标准流程',
    '{"operator": "AND", "items": []}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id AND f.is_default = 1
WHERE t.template_code = 'ECN_TEMPLATE';

-- ============================================================
-- 第四部分: 为 PROJECT_TEMPLATE 添加路由规则
-- ============================================================

-- 项目审批不需要路由规则,所有请求都走标准流程
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '默认流程', 1, '所有项目请求都走标准流程',
    '{"operator": "AND", "items": []}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id AND f.is_default = 1
WHERE t.template_code = 'PROJECT_TEMPLATE';

-- ============================================================
-- 第五部分: 为 TIMESHEET_TEMPLATE 添加路由规则
-- ============================================================

-- 工时审批不需要路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '默认流程', 1, '所有工时审批请求都走标准流程',
    '{"operator": "AND", "items": []}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id AND f.is_default = 1
WHERE t.template_code = 'TIMESHEET_TEMPLATE';

-- ============================================================
-- 第六部分: 为 TASK_TEMPLATE 添加路由规则
-- ============================================================

-- 任务审批不需要路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '默认流程', 1, '所有任务审批请求都走标准流程',
    '{"operator": "AND", "items": []}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id AND f.is_default = 1
WHERE t.template_code = 'TASK_TEMPLATE';

-- ============================================================
-- 迁移说明
-- ============================================================

-- 本次迁移完成以下内容：
--
-- 1. 清理旧模板：
--    - 删除无流程定义的 LEAVE_REQUEST 模板
--
-- 2. 补充节点配置：
--    - 为所有节点的 approver_config 填充 JSON 配置
--    - 确保审批人配置完整,便于运行时解析
--
-- 3. 添加默认路由规则：
--    - ECN_TEMPLATE: 所有请求走标准流程
--    - PROJECT_TEMPLATE: 所有请求走标准流程
--    - TIMESHEET_TEMPLATE: 所有请求走标准流程
--    - TASK_TEMPLATE: 所有请求走标准流程
--
-- 完成后的审批模板数量：10个
-- 完成后的路由规则数量：19个
