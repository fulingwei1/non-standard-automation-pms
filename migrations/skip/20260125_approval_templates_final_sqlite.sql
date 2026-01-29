-- 审批模板最终补充迁移
-- 创建日期: 2026-01-25
-- 描述: 为所有节点填充 approver_config 字段

-- ============================================================
-- 为 ECN_TEMPLATE 节点填充 approver_config
-- ============================================================

-- 技术评审节点
UPDATE approval_node_definitions
SET approver_config = '{"user_ids": []}'
WHERE node_code = 'TECH_REVIEW' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'ECN_TEMPLATE')
);

-- 部门会签节点
UPDATE approval_node_definitions
SET approver_config = '{"level": 1}'
WHERE node_code = 'DEPT_COUNTSIGN' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'ECN_TEMPLATE')
);

-- 最终审批节点
UPDATE approval_node_definitions
SET approver_config = '{"user_ids": []}'
WHERE node_code = 'FINAL_APPROVAL' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'ECN_TEMPLATE')
);

-- ============================================================
-- 为 TIMESHEET_TEMPLATE 节点填充 approver_config
-- ============================================================

UPDATE approval_node_definitions
SET approver_config = '{"level": 1}'
WHERE node_code = 'DIRECT_MANAGER' AND flow_id IN (
    SELECT id FROM approval_flow_definitions
    WHERE template_id IN (SELECT id FROM approval_templates WHERE template_code = 'TIMESHEET_TEMPLATE')
);

-- ============================================================
-- 迁移说明
-- ============================================================

-- 本次迁移完成以下内容：
--
-- 1. 填充 ECN_TEMPLATE 节点配置：
--    - 技术评审: FIXED_USER 类型,用户ID列表由发起人指定
--    - 部门会签: DEPARTMENT_HEAD 类型,向上查找1级
--    - 最终审批: FIXED_USER 类型,用户ID列表由发起人指定
--
-- 2. 填充 TIMESHEET_TEMPLATE 节点配置：
--    - 直属主管: DIRECT_MANAGER 类型,向上查找1级
--
-- 完成后所有节点的 approver_config 字段都已填充
-- 确保审批引擎能够正确解析审批人配置
