-- 为 User、Role、Permission 表添加性能优化索引
-- 数据库: MySQL
-- 日期: 2025-01-11

-- ====================
-- users 表索引
-- ====================

-- is_active 索引（优化活跃用户查询）
CREATE INDEX IF NOT EXISTS idx_user_active ON users (is_active);

-- department 索引（优化部门查询）
CREATE INDEX IF NOT EXISTS idx_user_department ON users (department);

-- email 索引（优化邮箱查找）
CREATE INDEX IF NOT EXISTS idx_user_email ON users (email);

-- ====================
-- roles 表索引
-- ====================

-- is_active 索引（优化活跃角色查询）
CREATE INDEX IF NOT EXISTS idx_role_active ON roles (is_active);

-- is_system 索引（优化系统角色筛选）
CREATE INDEX IF NOT EXISTS idx_role_system ON roles (is_system);

-- data_scope 索引（优化数据权限范围筛选）
CREATE INDEX IF NOT EXISTS idx_role_data_scope ON roles (data_scope);

-- ====================
-- permissions 表索引
-- ====================

-- is_active 索引（优化活跃权限查询）
CREATE INDEX IF NOT EXISTS idx_permission_active ON permissions (is_active);

-- module 索引（优化按模块查询权限）
CREATE INDEX IF NOT EXISTS idx_permission_module ON permissions (module);

-- ====================
-- role_permissions 表索引
-- ====================

-- role_id 索引（优化角色权限查询）
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions (role_id);

-- permission_id 索引（优化权限角色查询）
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions (permission_id);

-- ====================
-- user_roles 表索引
-- ====================

-- user_id 索引（优化用户角色查询）
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles (user_id);

-- role_id 索引（优化角色用户查询）
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles (role_id);

-- ====================
-- 验证索引创建
-- ====================

-- 查询 users 表的索引
SHOW INDEX FROM users WHERE Key_name LIKE 'idx_user_%';

-- 查询 roles 表的索引
SHOW INDEX FROM roles WHERE Key_name LIKE 'idx_role_%';

-- 查询 permissions 表的索引
SHOW INDEX FROM permissions WHERE Key_name LIKE 'idx_permission_%';

-- 查询 role_permissions 表的索引
SHOW INDEX FROM role_permissions WHERE Key_name LIKE 'idx_role_permissions_%';

-- 查询 user_roles 表的索引
SHOW INDEX FROM user_roles WHERE Key_name LIKE 'idx_user_roles_%';
