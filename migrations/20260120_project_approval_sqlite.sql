-- 项目审批功能迁移脚本 (SQLite)
-- 日期: 2026-01-20
-- 功能: 为项目表添加审批状态字段

-- 添加审批状态字段
ALTER TABLE projects ADD COLUMN approval_status VARCHAR(20) DEFAULT 'NONE';
-- 注释: 审批状态：NONE/PENDING/APPROVED/REJECTED

-- 添加审批记录ID字段
ALTER TABLE projects ADD COLUMN approval_record_id INTEGER REFERENCES approval_records(id);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_approval ON projects(approval_status, approval_record_id);

-- 为项目审批创建默认工作流
INSERT INTO approval_workflows (workflow_type, workflow_name, description, is_active, created_at, updated_at)
SELECT 'PROJECT', '项目审批工作流', '项目创建或变更时的多级审批流程', 1, datetime('now'), datetime('now')
WHERE NOT EXISTS (SELECT 1 FROM approval_workflows WHERE workflow_type = 'PROJECT');

-- 获取刚创建的工作流ID并添加默认步骤
-- 注意: SQLite不支持变量，需要使用子查询
INSERT INTO approval_workflow_steps (workflow_id, step_order, step_name, approver_role, is_required, can_delegate, can_withdraw, created_at, updated_at)
SELECT
    (SELECT id FROM approval_workflows WHERE workflow_type = 'PROJECT' LIMIT 1),
    1,
    '部门经理审批',
    'DEPT_MANAGER',
    1,
    1,
    1,
    datetime('now'),
    datetime('now')
WHERE NOT EXISTS (
    SELECT 1 FROM approval_workflow_steps
    WHERE workflow_id = (SELECT id FROM approval_workflows WHERE workflow_type = 'PROJECT' LIMIT 1)
    AND step_order = 1
);

INSERT INTO approval_workflow_steps (workflow_id, step_order, step_name, approver_role, is_required, can_delegate, can_withdraw, created_at, updated_at)
SELECT
    (SELECT id FROM approval_workflows WHERE workflow_type = 'PROJECT' LIMIT 1),
    2,
    'PMO审批',
    'PMO_MANAGER',
    1,
    1,
    1,
    datetime('now'),
    datetime('now')
WHERE NOT EXISTS (
    SELECT 1 FROM approval_workflow_steps
    WHERE workflow_id = (SELECT id FROM approval_workflows WHERE workflow_type = 'PROJECT' LIMIT 1)
    AND step_order = 2
);
