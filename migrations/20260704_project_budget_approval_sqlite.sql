-- MISC-21: 项目预算审批接入统一审批引擎，并修正历史预算总额口径

UPDATE project_budgets
SET total_amount = (
    SELECT COALESCE(SUM(i.budget_amount), 0)
    FROM project_budget_items i
    WHERE i.budget_id = project_budgets.id
)
WHERE EXISTS (
    SELECT 1
    FROM project_budget_items i
    WHERE i.budget_id = project_budgets.id
)
AND ABS(
    COALESCE(total_amount, 0) - (
        SELECT COALESCE(SUM(i.budget_amount), 0)
        FROM project_budget_items i
        WHERE i.budget_id = project_budgets.id
    )
) > 0.01;

INSERT OR IGNORE INTO approval_templates (
    template_code,
    template_name,
    category,
    description,
    entity_type,
    is_published,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'TPL_PROJECT_BUDGET',
    '项目预算审批',
    'FINANCE',
    '项目预算提交与审批流程。',
    'PROJECT_BUDGET',
    1,
    1,
    datetime('now'),
    datetime('now')
);

INSERT INTO approval_flow_definitions (
    template_id,
    flow_name,
    description,
    is_default,
    version,
    is_active,
    created_at,
    updated_at
)
SELECT
    t.id,
    '默认项目预算审批',
    '项目预算默认审批流程。',
    1,
    1,
    1,
    datetime('now'),
    datetime('now')
FROM approval_templates t
WHERE t.template_code = 'TPL_PROJECT_BUDGET'
  AND NOT EXISTS (
      SELECT 1
      FROM approval_flow_definitions f
      WHERE f.template_id = t.id
        AND f.flow_name = '默认项目预算审批'
  );

INSERT INTO approval_node_definitions (
    flow_id,
    node_code,
    node_name,
    node_order,
    node_type,
    approval_mode,
    is_active,
    approver_type,
    approver_config,
    notify_config,
    created_at,
    updated_at
)
SELECT
    f.id,
    'PROJECT_BUDGET_FINANCE_REVIEW',
    '财务负责人审批',
    1,
    'APPROVAL',
    'SINGLE',
    1,
    CASE WHEN u.id IS NOT NULL THEN 'FIXED_USER' ELSE 'ROLE' END,
    CASE
        WHEN u.id IS NOT NULL THEN '{"user_ids":[' || u.id || ']}'
        ELSE '{"role_codes":["ADMIN"]}'
    END,
    '{}',
    datetime('now'),
    datetime('now')
FROM approval_flow_definitions f
JOIN approval_templates t ON t.id = f.template_id
LEFT JOIN users u ON u.username = 'admin'
WHERE t.template_code = 'TPL_PROJECT_BUDGET'
  AND f.flow_name = '默认项目预算审批'
  AND NOT EXISTS (
      SELECT 1
      FROM approval_node_definitions n
      WHERE n.flow_id = f.id
        AND n.node_code = 'PROJECT_BUDGET_FINANCE_REVIEW'
  );
