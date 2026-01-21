-- 数据迁移脚本: task_approval_workflows -> 统一审批系统
-- 创建日期: 2026-01-21
-- 描述: 将 task_approval_workflows 的 59 条记录迁移到新的统一审批表

-- ============================================================
-- 步骤 1: 迁移到 approval_instances
-- ============================================================
INSERT INTO approval_instances (
    instance_no,
    template_id,
    entity_type,
    entity_id,
    initiator_id,
    form_data,
    status,
    title,
    summary,
    submitted_at,
    completed_at,
    created_at,
    updated_at
)
SELECT
    'AP-TASK-' || printf('%06d', taw.id),  -- 生成唯一实例编号
    9,                                      -- TASK_APPROVAL 模板 ID
    'TASK',                                 -- 业务实体类型
    taw.task_id,                            -- 业务实体 ID
    taw.submitted_by,                       -- 发起人
    taw.task_details,                       -- 任务详情作为表单数据
    CASE
        WHEN taw.approval_status = 'APPROVED' THEN 'APPROVED'
        WHEN taw.approval_status = 'REJECTED' THEN 'REJECTED'
        ELSE 'PENDING'
    END,                                    -- 状态映射
    COALESCE(json_extract(taw.task_details, '$.title'), '任务审批'),  -- 标题
    taw.submit_note,                        -- 提交理由作为摘要
    taw.submitted_at,
    CASE WHEN taw.approval_status IN ('APPROVED', 'REJECTED') THEN taw.approved_at END,
    taw.created_at,
    taw.updated_at
FROM task_approval_workflows taw
WHERE NOT EXISTS (
    -- 防止重复迁移
    SELECT 1 FROM approval_instances ai
    WHERE ai.entity_type = 'TASK' AND ai.entity_id = taw.task_id
);

-- ============================================================
-- 步骤 2: 为每个实例创建审批任务
-- ============================================================
INSERT INTO approval_tasks (
    instance_id,
    node_id,
    task_type,
    assignee_id,
    status,
    action,
    comment,
    completed_at,
    created_at,
    updated_at
)
SELECT
    ai.id,                                  -- 审批实例 ID
    1,                                      -- 默认节点 ID (会在后续创建流程时修正)
    'APPROVAL',                             -- 任务类型
    taw.approver_id,                        -- 审批人
    CASE
        WHEN taw.approval_status = 'APPROVED' THEN 'COMPLETED'
        WHEN taw.approval_status = 'REJECTED' THEN 'COMPLETED'
        ELSE 'PENDING'
    END,                                    -- 任务状态
    CASE
        WHEN taw.approval_status = 'APPROVED' THEN 'APPROVE'
        WHEN taw.approval_status = 'REJECTED' THEN 'REJECT'
        ELSE NULL
    END,                                    -- 操作
    COALESCE(taw.approval_note, taw.rejection_reason),  -- 意见
    CASE WHEN taw.approval_status IN ('APPROVED', 'REJECTED') THEN taw.approved_at END,
    taw.created_at,
    taw.updated_at
FROM task_approval_workflows taw
JOIN approval_instances ai ON ai.entity_type = 'TASK' AND ai.entity_id = taw.task_id
WHERE taw.approver_id IS NOT NULL
AND NOT EXISTS (
    -- 防止重复迁移
    SELECT 1 FROM approval_tasks at
    WHERE at.instance_id = ai.id AND at.assignee_id = taw.approver_id
);

-- ============================================================
-- 步骤 3: 记录审批操作日志 (已完成的审批)
-- ============================================================

-- 3.1 提交操作日志
INSERT INTO approval_action_logs (
    instance_id,
    operator_id,
    action,
    comment,
    after_status,
    action_at,
    created_at,
    updated_at
)
SELECT
    ai.id,
    taw.submitted_by,
    'SUBMIT',
    taw.submit_note,
    'PENDING',
    taw.submitted_at,
    taw.submitted_at,
    taw.submitted_at
FROM task_approval_workflows taw
JOIN approval_instances ai ON ai.entity_type = 'TASK' AND ai.entity_id = taw.task_id
WHERE NOT EXISTS (
    SELECT 1 FROM approval_action_logs al
    WHERE al.instance_id = ai.id AND al.action = 'SUBMIT'
);

-- 3.2 审批/驳回操作日志
INSERT INTO approval_action_logs (
    instance_id,
    operator_id,
    action,
    comment,
    before_status,
    after_status,
    action_at,
    created_at,
    updated_at
)
SELECT
    ai.id,
    taw.approver_id,
    CASE
        WHEN taw.approval_status = 'APPROVED' THEN 'APPROVE'
        WHEN taw.approval_status = 'REJECTED' THEN 'REJECT'
    END,
    COALESCE(taw.approval_note, taw.rejection_reason),
    'PENDING',
    taw.approval_status,
    taw.approved_at,
    taw.approved_at,
    taw.approved_at
FROM task_approval_workflows taw
JOIN approval_instances ai ON ai.entity_type = 'TASK' AND ai.entity_id = taw.task_id
WHERE taw.approval_status IN ('APPROVED', 'REJECTED')
AND taw.approver_id IS NOT NULL
AND taw.approved_at IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM approval_action_logs al
    WHERE al.instance_id = ai.id AND al.action IN ('APPROVE', 'REJECT')
);

-- ============================================================
-- 验证迁移结果
-- ============================================================
-- 运行以下查询验证迁移:
-- SELECT COUNT(*) FROM approval_instances WHERE entity_type = 'TASK';
-- SELECT COUNT(*) FROM approval_tasks WHERE instance_id IN (SELECT id FROM approval_instances WHERE entity_type = 'TASK');
-- SELECT COUNT(*) FROM approval_action_logs WHERE instance_id IN (SELECT id FROM approval_instances WHERE entity_type = 'TASK');
