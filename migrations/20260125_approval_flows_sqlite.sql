-- 统一审批系统流程定义迁移
-- 创建日期: 2026-01-25
-- 描述: 为 ECN, QUOTE, CONTRACT, INVOICE 创建默认审批流程

-- ============================================================
-- 1. 插入审批模板
-- ============================================================

-- ECN 审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at
) VALUES (
    'ECN_TEMPLATE', '工程变更审批模板', 'PROJECT',
    'ECN标准的工程变更审批流程，支持多部门会签',
    'ECN', 1, 1, CURRENT_TIMESTAMP
);

-- QUOTE 审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at
) VALUES (
    'QUOTE_TEMPLATE', '报价审批模板', 'SALES',
    '报价单审批流程，根据报价金额自动路由到不同级别',
    'QUOTE', 1, 1, CURRENT_TIMESTAMP
);

-- CONTRACT 审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at
) VALUES (
    'CONTRACT_TEMPLATE', '合同审批模板', 'SALES',
    '合同审批流程，根据合同金额自动路由到不同级别',
    'CONTRACT', 1, 1, CURRENT_TIMESTAMP
);

-- INVOICE 审批模板
INSERT OR IGNORE INTO approval_templates (
    template_code, template_name, category, description,
    entity_type, is_published, is_active, created_at
) VALUES (
    'INVOICE_TEMPLATE', '发票审批模板', 'SALES',
    '发票审批流程，根据发票金额自动路由到不同级别',
    'INVOICE', 1, 1, CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. 插入审批流程定义
-- ============================================================

-- ECN 审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at
) SELECT id, 'ECN标准流程', 'ECN标准审批流程，包含技术评审、部门会签、最终审批三个层级', 1, 1, 1, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'ECN_TEMPLATE';

-- QUOTE 审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at
) SELECT id, '报价审批流程', '根据报价金额自动路由到不同审批级别', 1, 1, 1, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'QUOTE_TEMPLATE';

-- CONTRACT 审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at
) SELECT id, '合同审批流程', '根据合同金额自动路由到不同审批级别', 1, 1, 1, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'CONTRACT_TEMPLATE';

-- INVOICE 审批流程
INSERT OR IGNORE INTO approval_flow_definitions (
    template_id, flow_name, description, is_default, version, is_active, created_at
) SELECT id, '发票审批流程', '根据发票金额自动路由到不同审批级别', 1, 1, 1, CURRENT_TIMESTAMP
FROM approval_templates
WHERE template_code = 'INVOICE_TEMPLATE';

-- ============================================================
-- 3. 插入审批节点定义
-- ============================================================

-- ECN 审批节点
INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'TECH_REVIEW', '技术评审', 1, 'APPROVAL', 'SINGLE', 'FIXED_USER', NULL, NULL, 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'ECN_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'DEPT_COUNTSIGN', '部门会签', 2, 'APPROVAL', 'AND_SIGN', 'DEPARTMENT_HEAD', NULL, NULL, 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'ECN_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'FINAL_APPROVAL', '最终审批', 3, 'APPROVAL', 'SINGLE', 'FIXED_USER', NULL, NULL, 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'ECN_TEMPLATE';

-- QUOTE 审批节点 (条件路由)
INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'SALES_MGR', '销售经理审批', 1, 'APPROVAL', 'SINGLE', 'ROLE', '"SALES_MANAGER"', '{{ amount | float < 100000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'QUOTE_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'SALES_DIRECTOR', '销售总监审批', 2, 'APPROVAL', 'SINGLE', 'ROLE', '"SALES_DIRECTOR"', '{{ amount | float >= 100000 and amount | float < 500000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'QUOTE_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'GM_APPROVAL', '总经理审批', 3, 'APPROVAL', 'SINGLE', 'ROLE', '"GENERAL_MANAGER"', '{{ amount | float >= 500000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'QUOTE_TEMPLATE';

-- CONTRACT 审批节点 (条件路由)
INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'SALES_MGR_CONTRACT', '销售经理审批', 1, 'APPROVAL', 'SINGLE', 'ROLE', '"SALES_MANAGER"', '{{ amount | float < 500000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'CONTRACT_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'SALES_DIRECTOR_CONTRACT', '销售总监审批', 2, 'APPROVAL', 'SINGLE', 'ROLE', '"SALES_DIRECTOR"', '{{ amount | float >= 500000 and amount | float < 1000000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'CONTRACT_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'GM_CONTRACT', '总经理审批', 3, 'APPROVAL', 'SINGLE', 'ROLE', '"GENERAL_MANAGER"', '{{ amount | float >= 1000000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'CONTRACT_TEMPLATE';

-- INVOICE 审批节点 (条件路由)
INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'FINANCE_MGR', '财务经理审批', 1, 'APPROVAL', 'SINGLE', 'ROLE', '"FINANCE_MANAGER"', '{{ amount | float < 100000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'INVOICE_TEMPLATE';

INSERT OR IGNORE INTO approval_node_definitions (flow_id, node_code, node_name, node_order, node_type, approval_mode, approver_type, approver_config, condition_expression, timeout_hours, created_at)
SELECT
    fd.id, 'FINANCE_DIRECTOR', '财务总监审批', 2, 'APPROVAL', 'SINGLE', 'ROLE', '"FINANCE_DIRECTOR"', '{{ amount | float >= 100000 }}', 24, CURRENT_TIMESTAMP
FROM approval_flow_definitions fd
JOIN approval_templates t ON fd.template_id = t.id
WHERE t.template_code = 'INVOICE_TEMPLATE';

-- ============================================================
-- 4. 创建索引（提高查询性能）
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_approval_node_flow ON approval_node_definitions(flow_id);
CREATE INDEX IF NOT EXISTS idx_approval_node_order ON approval_node_definitions(flow_id, node_order);
CREATE INDEX IF NOT EXISTS idx_approval_node_code ON approval_node_definitions(node_code);

-- ============================================================
-- 迁移说明
-- ============================================================

-- 本次迁移为统一审批系统创建了以下内容：
--
-- 1. 审批模板（4个）：
--    - ECN_TEMPLATE: 工程变更审批模板
--    - QUOTE_TEMPLATE: 报价审批模板
--    - CONTRACT_TEMPLATE: 合同审批模板
--    - INVOICE_TEMPLATE: 发票审批模板
--
-- 2. 审批流程定义（4个）：
--    - ECN标准流程: 包含技术评审、部门会签、最终审批
--    - 报价审批流程: 根据金额自动路由（<10万/10-50万/>=50万）
--    - 合同审批流程: 根据金额自动路由（<50万/50-100万/>=100万）
--    - 发票审批流程: 根据金额自动路由（<10万/>=10万）
--
-- 3. 审批节点（14个）：
--    ECN流程（3个节点）: 技术评审 -> 部门会签 -> 最终审批
--    QUOTE流程（3个节点）: 销售经理 -> 销售总监 -> 总经理
--    CONTRACT流程（3个节点）: 销售经理 -> 销售总监 -> 总经理
--    INVOICE流程（2个节点）: 财务经理 -> 财务总监
--
-- 所有节点超时设置为24小时
--
-- 使用方式：
-- 1. 提交审批时使用相应的模板代码（template_code）
-- 2. 系统会自动根据条件表达式路由到对应节点
-- 3. 审批完成后自动更新业务实体状态
