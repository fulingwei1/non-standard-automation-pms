-- 补充缺失的权限定义 (SQLite)
-- 日期: 2026-01-20
-- 说明: 添加代码中已使用但数据库中不存在的权限

BEGIN;

-- ============================================
-- 1. 系统管理模块权限（统一格式）
-- ============================================

INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('system:user:read', '用户查看', 'system', 'user', 'read', '查看用户信息'),
('system:user:create', '用户创建', 'system', 'user', 'create', '创建新用户'),
('system:user:update', '用户更新', 'system', 'user', 'update', '更新用户信息'),
('system:user:delete', '用户删除', 'system', 'user', 'delete', '删除用户'),
('system:role:create', '角色创建', 'system', 'role', 'create', '创建新角色'),
('system:role:update', '角色更新', 'system', 'role', 'update', '更新角色信息'),
('system:audit:read', '审计查看', 'system', 'audit', 'read', '查看审计日志');

-- ============================================
-- 2. 绩效管理模块权限
-- ============================================

INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('performance:manage', '绩效管理', 'performance', 'performance', 'manage', '绩效管理权限（包含所有操作）'),
('performance:evaluation:read', '绩效评估查看', 'performance', 'evaluation', 'read', '查看绩效评估'),
('performance:evaluation:create', '绩效评估创建', 'performance', 'evaluation', 'create', '创建绩效评估'),
('performance:evaluation:update', '绩效评估更新', 'performance', 'evaluation', 'update', '更新绩效评估'),
('performance:summary:read', '工作汇总查看', 'performance', 'summary', 'read', '查看工作汇总'),
('performance:summary:create', '工作汇总创建', 'performance', 'summary', 'create', '创建工作汇总'),
('performance:summary:update', '工作汇总更新', 'performance', 'summary', 'update', '更新工作汇总');

-- ============================================
-- 3. 项目管理模块扩展权限
-- ============================================

INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('project:erp:sync', 'ERP同步', 'project', 'erp', 'sync', '同步项目数据到ERP系统'),
('project:erp:update', 'ERP更新', 'project', 'erp', 'update', '更新ERP系统中的项目数据');

-- ============================================
-- 4. 工作日志模块权限
-- ============================================

INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('work_log:config:read', '工作日志配置查看', 'work_log', 'config', 'read', '查看工作日志配置'),
('work_log:config:create', '工作日志配置创建', 'work_log', 'config', 'create', '创建工作日志配置'),
('work_log:config:update', '工作日志配置更新', 'work_log', 'config', 'update', '更新工作日志配置');

-- ============================================
-- 5. 角色权限分配
-- ============================================

-- 系统管理员：所有权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'ADMIN'
  AND p.perm_code IN (
    'system:user:read', 'system:user:create', 'system:user:update', 'system:user:delete',
    'system:role:create', 'system:role:update',
    'system:audit:read',
    'performance:manage', 'performance:evaluation:read', 'performance:evaluation:create', 'performance:evaluation:update',
    'performance:summary:read', 'performance:summary:create', 'performance:summary:update',
    'project:erp:sync', 'project:erp:update',
    'work_log:config:read', 'work_log:config:create', 'work_log:config:update'
  );

-- 总经理：查看和审批权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'GM'
  AND p.perm_code IN (
    'system:user:read', 'system:role:read',
    'system:audit:read',
    'performance:evaluation:read', 'performance:summary:read',
    'project:erp:read'
  );

-- 项目经理：项目相关权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'PM'
  AND p.perm_code IN (
    'performance:evaluation:read', 'performance:summary:read', 'performance:summary:create',
    'project:erp:sync',
    'work_log:config:read'
  );

COMMIT;
