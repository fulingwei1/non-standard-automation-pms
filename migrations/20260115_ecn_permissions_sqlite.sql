-- ECN变更管理模块权限配置 (SQLite)
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 将ECN作为独立模块，配置权限并分配给相应角色
-- 注意：使用 perm_code / perm_name 列名

BEGIN;

-- ============================================
-- 1. ECN模块权限定义
-- ============================================

-- 使用旧表结构（perm_code）
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action) VALUES
('ecn:ecn:read', 'ECN查看', 'ecn', 'read'),
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
  AND p.perm_code LIKE 'ecn:%';

-- 总经理：查看、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'GM'
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'approve', 'reject')
    OR p.perm_code LIKE 'ecn:statistics:%'
    OR p.perm_code LIKE 'ecn:alert:%'
  );

-- 项目经理：ECN全流程管理（自己项目的ECN）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PM'
  AND p.module = 'ecn'
  AND p.perm_code NOT IN ('ecn:type:manage', 'ecn:matrix:manage', 'ecn:ecn:delete');

-- 计划管理（PMC）：查看、评估、执行权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PMC'
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit', 'update', 'complete')
    OR p.perm_code LIKE 'ecn:evaluation:%'
    OR p.perm_code LIKE 'ecn:task:%'
    OR p.perm_code LIKE 'ecn:sync:%'
    OR p.perm_code LIKE 'ecn:statistics:%'
  );

-- 质量工程师：查看、评估、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'QA'
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit', 'approve', 'reject')
    OR p.perm_code LIKE 'ecn:evaluation:%'
    OR p.perm_code LIKE 'ecn:approval:%'
    OR p.perm_code LIKE 'ecn:statistics:%'
  );

-- 采购专员：查看、评估、同步权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PU'
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'create', 'submit')
    OR p.perm_code LIKE 'ecn:evaluation:%'
    OR p.perm_code LIKE 'ecn:sync:purchase%'
    OR p.perm_code LIKE 'ecn:affected:%'
  );

-- 财务专员：查看、审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'FI'
  AND p.module = 'ecn'
  AND (
    p.action IN ('read', 'approve', 'reject')
    OR p.perm_code LIKE 'ecn:approval:%'
    OR p.perm_code LIKE 'ecn:statistics:%'
  );

COMMIT;
