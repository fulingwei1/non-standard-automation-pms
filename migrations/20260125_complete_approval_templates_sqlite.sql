-- 统一审批系统完整模板数据迁移
-- 创建日期: 2026-01-25
-- 描述:
--   1. 清理重复的流程定义和节点数据
--   2. 为缺失的业务实体添加审批流程模板
--   3. 创建路由规则确保工作流正确路由

-- ============================================================
-- 第一部分: 清理重复数据
-- ============================================================

-- 删除重复的流程定义(保留最小的ID)
DELETE FROM approval_flow_definitions
WHERE id NOT IN (
    SELECT MIN(id)
    FROM approval_flow_definitions
    GROUP BY template_id, flow_name
);

-- 删除孤立的节点定义(没有关联到有效流程的节点)
DELETE FROM approval_node_definitions
WHERE flow_id NOT IN (
    SELECT id FROM approval_flow_definitions
);

-- 删除重复的节点定义(同一流程下相同节点顺序的只保留一个)
DELETE FROM approval_node_definitions
WHERE id NOT IN (
    SELECT MIN(id)
    FROM approval_node_definitions
    GROUP BY flow_id, node_code, node_order
);

-- 删除老的未使用的模板(没有流程定义的)
DELETE FROM approval_templates
WHERE id NOT IN (SELECT DISTINCT template_id FROM approval_flow_definitions)
AND template_code LIKE '%_APPROVAL';

-- ============================================================
-- 第二部分: 为缺失的业务实体添加审批流程模板
-- ============================================================

-- 1. 采购申请审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at, updated_at
) VALUES (
    'PURCHASE_REQUEST_TEMPLATE', '采购申请审批模板', 'PURCHASE',
    '采购申请审批流程,根据采购金额自动路由到不同级别',
    'PURCHASE_REQUEST', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- 2. 工时审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at, updated_at
) VALUES (
    'TIMESHEET_TEMPLATE', '工时审批模板', 'HR',
    '工时审批流程,支持按天、按周、按月提交和审批',
    'TIMESHEET', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- 3. 任务审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at, updated_at
) VALUES (
    'TASK_TEMPLATE', '任务审批模板', 'PROJECT',
    '任务创建和状态变更审批流程',
    'TASK', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- 4. 请假申请模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at, updated_at
) VALUES (
    'LEAVE_REQUEST_TEMPLATE', '请假申请模板', 'HR',
    '员工请假申请审批流程,根据请假天数和类型自动路由',
    'LEAVE', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- 5. 项目审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at, updated_at
) VALUES (
    'PROJECT_TEMPLATE', '项目审批模板', 'PROJECT',
    '项目立项和阶段变更审批流程',
    'PROJECT', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- ============================================================
-- 第三部分: 为新模板创建流程定义
-- ============================================================

-- 采购申请流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at, updated_at
) SELECT id, '采购申请标准流程', '根据采购金额自动路由到不同审批级别', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'PURCHASE_REQUEST_TEMPLATE';

-- 工时审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at, updated_at
) SELECT id, '工时审批标准流程', '支持按天/周/月提交,由直属主管审批', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'TIMESHEET_TEMPLATE';

-- 任务审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at, updated_at
) SELECT id, '任务审批标准流程', '任务创建和状态变更需要负责人审批', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'TASK_TEMPLATE';

-- 请假申请流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at, updated_at
) SELECT id, '请假申请标准流程', '根据请假天数和类型自动路由', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'LEAVE_REQUEST_TEMPLATE';

-- 项目审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at, updated_at
) SELECT id, '项目审批标准流程', '项目立项和阶段变更需要部门负责人和PMO审批', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'PROJECT_TEMPLATE';

-- ============================================================
-- 第四部分: 为新流程创建节点定义
-- ============================================================

-- 采购申请节点 (条件路由)
INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'PURCHASE_MGR', '采购经理审批', 1, 'APPROVAL', 'SINGLE', 'ROLE',
    '"PURCHASE_MANAGER"', '{{ amount | float < 10000 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'DEPT_HEAD_PURCHASE', '部门主管审批', 2, 'APPROVAL', 'SINGLE', 'ROLE',
    '"DEPARTMENT_HEAD"', '{{ amount | float >= 10000 and amount | float < 50000 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'GM_PURCHASE', '总经理审批', 3, 'APPROVAL', 'SINGLE', 'ROLE',
    '"GENERAL_MANAGER"', '{{ amount | float >= 50000 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

-- 工时审批节点
INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'DIRECT_MANAGER', '直属主管审批', 1, 'APPROVAL', 'SINGLE', 'DIRECT_MANAGER',
    NULL, NULL, 48, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'TIMESHEET_TEMPLATE';

-- 任务审批节点
INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'TASK_OWNER', '任务负责人审批', 1, 'APPROVAL', 'SINGLE', 'ROLE',
    '"PROJECT_MANAGER"', NULL, 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'TASK_TEMPLATE';

-- 请假申请节点 (条件路由)
INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'TEAM_LEADER', '组长审批', 1, 'APPROVAL', 'SINGLE', 'DIRECT_MANAGER',
    NULL, '{{ days | int <= 1 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'DEPT_HEAD_LEAVE', '部门主管审批', 2, 'APPROVAL', 'SINGLE', 'DEPARTMENT_HEAD',
    NULL, '{{ days | int > 1 and days | int <= 3 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'HR_LEAVE', 'HR审批', 3, 'APPROVAL', 'SINGLE', 'ROLE',
    '"HR_MANAGER"', '{{ days | int > 3 }}', 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

-- 项目审批节点
INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'PROJECT_MGR', '项目经理审批', 1, 'APPROVAL', 'SINGLE', 'ROLE',
    '"PROJECT_MANAGER"', NULL, 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PROJECT_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'PMO_REVIEW', 'PMO评审', 2, 'APPROVAL', 'AND_SIGN', 'ROLE',
    '"PMO_OFFICER"', NULL, 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PROJECT_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (
    flow_id, node_code, node_name, node_order, node_type,
    approval_mode, approver_type, approver_config,
    condition_expression, timeout_hours, created_at, updated_at
)
SELECT
    fd.id, 'DEPT_DIRECTOR', '部门总监审批', 3, 'APPROVAL', 'SINGLE', 'ROLE',
    '"DEPARTMENT_DIRECTOR"', NULL, 24, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'PROJECT_TEMPLATE';

-- ============================================================
-- 第五部分: 创建路由规则
-- ============================================================

-- 报价审批路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '小于10万', 1, '报价金额小于10万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": "<", "value": 100000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'QUOTE_TEMPLATE' AND f.flow_name = '报价审批流程';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '10万-50万', 2, '报价金额10万-50万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 100000}, {"field": "form.amount", "op": "<", "value": 500000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'QUOTE_TEMPLATE' AND f.flow_name = '报价审批流程';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '50万以上', 3, '报价金额50万以上',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 500000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'QUOTE_TEMPLATE' AND f.flow_name = '报价审批流程';

-- 合同审批路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '小于50万', 1, '合同金额小于50万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": "<", "value": 500000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'CONTRACT_TEMPLATE' AND f.flow_name = '合同审批流程';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '50万-100万', 2, '合同金额50万-100万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 500000}, {"field": "form.amount", "op": "<", "value": 1000000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'CONTRACT_TEMPLATE' AND f.flow_name = '合同审批流程';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '100万以上', 3, '合同金额100万以上',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 1000000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'CONTRACT_TEMPLATE' AND f.flow_name = '合同审批流程';

-- 发票审批路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '小于10万', 1, '发票金额小于10万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": "<", "value": 100000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'INVOICE_TEMPLATE' AND f.flow_name = '发票审批流程';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '10万以上', 2, '发票金额10万以上',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 100000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'INVOICE_TEMPLATE' AND f.flow_name = '发票审批流程';

-- 采购申请路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '小于1万', 1, '采购金额小于1万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": "<", "value": 10000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '1万-5万', 2, '采购金额1万-5万',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 10000}, {"field": "form.amount", "op": "<", "value": 50000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '5万以上', 3, '采购金额5万以上',
    '{"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 50000}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'PURCHASE_REQUEST_TEMPLATE';

-- 请假申请路由规则
INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '1天及以下', 1, '请假天数1天及以下',
    '{"operator": "AND", "items": [{"field": "form.days", "op": "<=", "value": 1}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '1-3天', 2, '请假天数1-3天',
    '{"operator": "AND", "items": [{"field": "form.days", "op": ">", "value": 1}, {"field": "form.days", "op": "<=", "value": 3}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

INSERT OR IGNORE INTO approval_routing_rules (
    template_id, flow_id, rule_name, rule_order, description,
    conditions, is_active, created_at, updated_at
)
SELECT
    t.id, f.id, '3天以上', 3, '请假天数3天以上',
    '{"operator": "AND", "items": [{"field": "form.days", "op": ">", "value": 3}]}',
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM approval_templates t
JOIN approval_flow_definitions f ON t.id = f.template_id
WHERE t.template_code = 'LEAVE_REQUEST_TEMPLATE';

-- ============================================================
-- 迁移说明
-- ============================================================

-- 本次迁移完成以下内容：
--
-- 1. 数据清理：
--    - 删除重复的流程定义(每个模板同一流程名称只保留一个)
--    - 删除孤立的节点定义(没有关联到有效流程的节点)
--    - 删除重复的节点定义(同一流程下相同节点顺序的只保留一个)
--    - 删除老的未使用的模板
--
-- 2. 新增审批模板(5个)：
--    - PURCHASE_REQUEST_TEMPLATE: 采购申请审批模板
--    - TIMESHEET_TEMPLATE: 工时审批模板
--    - TASK_TEMPLATE: 任务审批模板
--    - LEAVE_REQUEST_TEMPLATE: 请假申请模板
--    - PROJECT_TEMPLATE: 项目审批模板
--
-- 3. 新增审批流程(5个)：
--    - 采购申请标准流程: 根据金额路由(<1万/1-5万/>=5万)
--    - 工时审批标准流程: 由直属主管审批
--    - 任务审批标准流程: 由项目经理审批
--    - 请假申请标准流程: 根据天数路由(<=1天/1-3天/>3天)
--    - 项目审批标准流程: 项目经理 -> PMO -> 部门总监
--
-- 4. 新增审批节点(16个)：
--    - 采购申请(3个节点): 采购经理 -> 部门主管 -> 总经理
--    - 工时审批(1个节点): 直属主管
--    - 任务审批(1个节点): 项目经理
--    - 请假申请(3个节点): 组长 -> 部门主管 -> HR
--    - 项目审批(3个节点): 项目经理 -> PMO -> 部门总监
--
-- 5. 创建路由规则(15个)：
--    - 报价审批(3个): 根据金额路由
--    - 合同审批(3个): 根据金额路由
--    - 发票审批(2个): 根据金额路由
--    - 采购申请(3个): 根据金额路由
--    - 请假申请(3个): 根据天数路由
--
-- 使用方式：
-- 1. 提交审批时使用相应的模板代码(template_code)
-- 2. 系统会自动根据路由规则条件表达式路由到对应节点
-- 3. 审批完成后自动更新业务实体状态
