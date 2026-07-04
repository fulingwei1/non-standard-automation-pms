-- MISC-19: 发货单审批接入统一审批引擎

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
    'TPL_DELIVERY_ORDER',
    '发货单审批',
    'BUSINESS',
    '商务支持发货单审批流程。',
    'DELIVERY_ORDER',
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
    '默认发货单审批',
    '商务支持发货单默认审批流程。',
    1,
    1,
    1,
    datetime('now'),
    datetime('now')
FROM approval_templates t
WHERE t.template_code = 'TPL_DELIVERY_ORDER'
  AND NOT EXISTS (
      SELECT 1
      FROM approval_flow_definitions f
      WHERE f.template_id = t.id
        AND f.flow_name = '默认发货单审批'
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
    'DELIVERY_ORDER_MANAGER_REVIEW',
    '发货负责人审批',
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
WHERE t.template_code = 'TPL_DELIVERY_ORDER'
  AND f.flow_name = '默认发货单审批'
  AND NOT EXISTS (
      SELECT 1
      FROM approval_node_definitions n
      WHERE n.flow_id = f.id
        AND n.node_code = 'DELIVERY_ORDER_MANAGER_REVIEW'
  );
