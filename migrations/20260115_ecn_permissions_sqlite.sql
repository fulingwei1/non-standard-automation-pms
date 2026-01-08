-- ECN变更管理模块权限配置 (SQLite)
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 将ECN作为独立模块，配置权限并分配给相应角色
-- 注意：兼容新旧两种表结构（perm_code 或 permission_code）

BEGIN;

-- ============================================
-- 1. ECN模块权限定义
-- ============================================

-- 先检查表结构，如果使用新表结构（permission_code），使用新字段
-- 如果使用旧表结构（perm_code），使用旧字段

-- 尝试使用新表结构（permission_code）
INSERT OR IGNORE INTO permissions (permission_code, permission_name, module, resource, action, description, is_active) 
SELECT 'ecn:ecn:read', 'ECN查看', 'ecn', 'ecn', 'read', '查看ECN列表和详情', 1
WHERE EXISTS (
    SELECT 1 FROM sqlite_master 
    WHERE type='table' AND name='permissions' 
    AND sql LIKE '%permission_code%'
);

-- 如果新表结构不存在，使用旧表结构（perm_code）
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action)
SELECT 'ecn:ecn:read', 'ECN查看', 'ecn', 'read'
WHERE NOT EXISTS (
    SELECT 1 FROM sqlite_master 
    WHERE type='table' AND name='permissions' 
    AND sql LIKE '%permission_code%'
);

-- 批量插入所有ECN权限（根据表结构选择）
-- 新表结构版本
INSERT OR IGNORE INTO permissions (permission_code, permission_name, module, resource, action, description, is_active) VALUES
('ecn:ecn:read', 'ECN查看', 'ecn', 'ecn', 'read', '查看ECN列表和详情', 1),
('ecn:ecn:create', 'ECN创建', 'ecn', 'ecn', 'create', '创建ECN申请', 1),
('ecn:ecn:update', 'ECN修改', 'ecn', 'ecn', 'update', '修改ECN信息（草稿状态）', 1),
('ecn:ecn:submit', 'ECN提交', 'ecn', 'ecn', 'submit', '提交ECN进入评估流程', 1),
('ecn:ecn:cancel', 'ECN取消', 'ecn', 'ecn', 'cancel', '取消ECN申请', 1),
('ecn:ecn:delete', 'ECN删除', 'ecn', 'ecn', 'delete', '删除ECN（仅管理员）', 1),
('ecn:evaluation:read', '评估查看', 'ecn', 'evaluation', 'read', '查看评估记录', 1),
('ecn:evaluation:create', '评估创建', 'ecn', 'evaluation', 'create', '创建评估记录', 1),
('ecn:evaluation:submit', '评估提交', 'ecn', 'evaluation', 'submit', '提交评估结果', 1),
('ecn:approval:read', '审批查看', 'ecn', 'approval', 'read', '查看审批记录', 1),
('ecn:approval:approve', '审批通过', 'ecn', 'approval', 'approve', '审批通过ECN', 1),
('ecn:approval:reject', '审批驳回', 'ecn', 'approval', 'reject', '驳回ECN', 1),
('ecn:task:read', '任务查看', 'ecn', 'task', 'read', '查看执行任务', 1),
('ecn:task:create', '任务创建', 'ecn', 'task', 'create', '创建执行任务', 1),
('ecn:task:update', '任务更新', 'ecn', 'task', 'update', '更新任务进度', 1),
('ecn:task:complete', '任务完成', 'ecn', 'task', 'complete', '完成任务', 1),
('ecn:affected:read', '影响分析查看', 'ecn', 'affected', 'read', '查看受影响物料和订单', 1),
('ecn:affected:manage', '影响分析管理', 'ecn', 'affected', 'manage', '管理受影响物料和订单', 1),
('ecn:sync:bom', 'BOM同步', 'ecn', 'sync', 'bom', '同步ECN变更到BOM', 1),
('ecn:sync:project', '项目同步', 'ecn', 'sync', 'project', '同步ECN变更到项目', 1),
('ecn:sync:purchase', '采购同步', 'ecn', 'sync', 'purchase', '同步ECN变更到采购', 1),
('ecn:type:read', '类型配置查看', 'ecn', 'type', 'read', '查看ECN类型配置', 1),
('ecn:type:manage', '类型配置管理', 'ecn', 'type', 'manage', '管理ECN类型配置', 1),
('ecn:matrix:read', '审批矩阵查看', 'ecn', 'matrix', 'read', '查看审批矩阵配置', 1),
('ecn:matrix:manage', '审批矩阵管理', 'ecn', 'matrix', 'manage', '管理审批矩阵配置', 1),
('ecn:statistics:read', '统计查看', 'ecn', 'statistics', 'read', '查看ECN统计报表', 1),
('ecn:alert:read', '超时提醒查看', 'ecn', 'alert', 'read', '查看ECN超时提醒', 1);

-- 旧表结构版本（如果使用 perm_code）
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action)
SELECT 'ecn:ecn:read', 'ECN查看', 'ecn', 'read'
WHERE NOT EXISTS (
    SELECT 1 FROM permissions WHERE perm_code = 'ecn:ecn:read' OR permission_code = 'ecn:ecn:read'
);

INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action) VALUES
('ecn:ecn:create', 'ECN创建', 'ecn', 'create'),
('ecn:ecn:update', 'ECN修改', 'ecn', 'update'),
('ecn:ecn:submit', 'ECN提交', 'ecn', 'submit'),
('ecn:ecn:cancel', 'ECN取消', 'ecn', 'cancel'),
('ecn:ecn:delete', 'ECN删除', 'ecn', 'delete'),
('ecn:evaluation:read', '评估查看', 'ecn', 'read'),
('ecn:evaluation:create', '评估创建', 'ecn', 'create'),
('ecn:evaluation:submit', '评估提交', 'ecn', 'submit'),
('ecn:approval:read', '审批查看', 'ecn', 'read'),
('ecn:approval:approve', '审批通过', 'ecn', 'approve'),
('ecn:approval:reject', '审批驳回', 'ecn', 'reject'),
('ecn:task:read', '任务查看', 'ecn', 'read'),
('ecn:task:create', '任务创建', 'ecn', 'create'),
('ecn:task:update', '任务更新', 'ecn', 'update'),
('ecn:task:complete', '任务完成', 'ecn', 'complete'),
('ecn:affected:read', '影响分析查看', 'ecn', 'read'),
('ecn:affected:manage', '影响分析管理', 'ecn', 'manage'),
('ecn:sync:bom', 'BOM同步', 'ecn', 'bom'),
('ecn:sync:project', '项目同步', 'ecn', 'project'),
('ecn:sync:purchase', '采购同步', 'ecn', 'purchase'),
('ecn:type:read', '类型配置查看', 'ecn', 'read'),
('ecn:type:manage', '类型配置管理', 'ecn', 'manage'),
('ecn:matrix:read', '审批矩阵查看', 'ecn', 'read'),
('ecn:matrix:manage', '审批矩阵管理', 'ecn', 'manage'),
('ecn:statistics:read', '统计查看', 'ecn', 'read'),
('ecn:alert:read', '超时提醒查看', 'ecn', 'read');

-- ============================================
-- 2. 角色权限分配
-- ============================================

-- 系统管理员：所有ECN权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'ADMIN' 
  AND p.module = 'ecn'
  AND ((p.permission_code LIKE 'ecn:%' AND p.permission_code IS NOT NULL)
       OR (p.perm_code LIKE 'ecn:%' AND p.perm_code IS NOT NULL));

-- 总经理：查看、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'GM' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'approve', 'reject') 
    OR (p.permission_code IS NOT NULL AND (p.permission_code LIKE 'ecn:statistics:%' OR p.permission_code LIKE 'ecn:alert:%'))
    OR (p.perm_code IS NOT NULL AND (p.perm_code LIKE 'ecn:statistics:%' OR p.perm_code LIKE 'ecn:alert:%'))
  );

-- 项目经理：ECN全流程管理（自己项目的ECN）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PM' 
  AND p.module = 'ecn'
  AND (
    (p.permission_code IS NOT NULL AND p.permission_code NOT IN ('ecn:type:manage', 'ecn:matrix:manage', 'ecn:ecn:delete'))
    OR (p.perm_code IS NOT NULL AND p.perm_code NOT IN ('ecn:type:manage', 'ecn:matrix:manage', 'ecn:ecn:delete'))
  );

-- 计划管理（PMC）：查看、评估、执行权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PMC' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit', 'update', 'complete') 
    OR (p.permission_code IS NOT NULL AND (
        p.permission_code LIKE 'ecn:evaluation:%'
        OR p.permission_code LIKE 'ecn:task:%'
        OR p.permission_code LIKE 'ecn:sync:%'
        OR p.permission_code LIKE 'ecn:statistics:%'
    ))
    OR (p.perm_code IS NOT NULL AND (
        p.perm_code LIKE 'ecn:evaluation:%'
        OR p.perm_code LIKE 'ecn:task:%'
        OR p.perm_code LIKE 'ecn:sync:%'
        OR p.perm_code LIKE 'ecn:statistics:%'
    ))
  );

-- 工程师：创建、查看、评估、执行权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'ENGINEER' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit', 'update', 'complete')
    OR (p.permission_code IS NOT NULL AND (
        p.permission_code LIKE 'ecn:evaluation:%'
        OR p.permission_code LIKE 'ecn:task:%'
        OR p.permission_code LIKE 'ecn:affected:%'
    ))
    OR (p.perm_code IS NOT NULL AND (
        p.perm_code LIKE 'ecn:evaluation:%'
        OR p.perm_code LIKE 'ecn:task:%'
        OR p.perm_code LIKE 'ecn:affected:%'
    ))
  );

-- 质量工程师：查看、评估、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'QA' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit', 'approve', 'reject')
    OR (p.permission_code IS NOT NULL AND (
        p.permission_code LIKE 'ecn:evaluation:%'
        OR p.permission_code LIKE 'ecn:approval:%'
        OR p.permission_code LIKE 'ecn:statistics:%'
    ))
    OR (p.perm_code IS NOT NULL AND (
        p.perm_code LIKE 'ecn:evaluation:%'
        OR p.perm_code LIKE 'ecn:approval:%'
        OR p.perm_code LIKE 'ecn:statistics:%'
    ))
  );

-- 采购专员：查看、评估、同步权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PURCHASER' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit')
    OR (p.permission_code IS NOT NULL AND (
        p.permission_code LIKE 'ecn:evaluation:%'
        OR p.permission_code LIKE 'ecn:sync:purchase%'
        OR p.permission_code LIKE 'ecn:affected:%'
    ))
    OR (p.perm_code IS NOT NULL AND (
        p.perm_code LIKE 'ecn:evaluation:%'
        OR p.perm_code LIKE 'ecn:sync:purchase%'
        OR p.perm_code LIKE 'ecn:affected:%'
    ))
  );

-- 财务专员：查看、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'FINANCE' 
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'approve', 'reject')
    OR (p.permission_code IS NOT NULL AND (
        p.permission_code LIKE 'ecn:approval:%'
        OR p.permission_code LIKE 'ecn:statistics:%'
    ))
    OR (p.perm_code IS NOT NULL AND (
        p.perm_code LIKE 'ecn:approval:%'
        OR p.perm_code LIKE 'ecn:statistics:%'
    ))
  );

COMMIT;
