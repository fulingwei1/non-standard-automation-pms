-- ============================================================
-- 权限系统多租户增强迁移脚本 (SQLite)
-- 日期: 2026-01-27
-- 描述: 为权限系统添加完整的多租户支持
-- 涉及表: api_permissions, data_scope_rules, menu_permissions
-- ============================================================

-- ============================================================
-- 第一部分：api_permissions 表
-- ============================================================

-- 1.1 添加 tenant_id 字段
ALTER TABLE api_permissions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);

-- 1.2 添加 is_system 列（标识系统预置权限）
ALTER TABLE api_permissions ADD COLUMN is_system BOOLEAN DEFAULT 0;

-- 1.3 删除旧的唯一约束（如果存在）
DROP INDEX IF EXISTS ix_api_permissions_perm_code;

-- 1.4 创建新的复合唯一索引（租户内唯一）
CREATE UNIQUE INDEX IF NOT EXISTS uk_tenant_perm_code
ON api_permissions(tenant_id, perm_code);

-- 1.5 创建租户索引（加速租户权限查询）
CREATE INDEX IF NOT EXISTS idx_api_perm_tenant
ON api_permissions(tenant_id);

-- 1.6 创建模块索引
CREATE INDEX IF NOT EXISTS idx_api_perm_module
ON api_permissions(module);

-- 1.7 将现有权限标记为系统级权限
UPDATE api_permissions
SET is_system = 1, tenant_id = NULL
WHERE tenant_id IS NULL;

-- ============================================================
-- 第二部分：data_scope_rules 表
-- ============================================================

-- 2.1 添加 tenant_id 字段
ALTER TABLE data_scope_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);

-- 2.2 添加 is_system 列
ALTER TABLE data_scope_rules ADD COLUMN is_system BOOLEAN DEFAULT 0;

-- 2.3 删除旧的唯一约束
DROP INDEX IF EXISTS ix_data_scope_rules_rule_code;

-- 2.4 创建新的复合唯一索引（租户内唯一）
CREATE UNIQUE INDEX IF NOT EXISTS uk_tenant_rule_code
ON data_scope_rules(tenant_id, rule_code);

-- 2.5 创建租户索引
CREATE INDEX IF NOT EXISTS idx_dsr_tenant
ON data_scope_rules(tenant_id);

-- 2.6 将现有规则标记为系统级规则
UPDATE data_scope_rules
SET is_system = 1, tenant_id = NULL
WHERE tenant_id IS NULL;

-- ============================================================
-- 第三部分：menu_permissions 表
-- ============================================================

-- 3.1 添加 tenant_id 字段
ALTER TABLE menu_permissions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);

-- 3.2 添加 is_system 列
ALTER TABLE menu_permissions ADD COLUMN is_system BOOLEAN DEFAULT 0;

-- 3.3 删除旧的唯一约束
DROP INDEX IF EXISTS ix_menu_permissions_menu_code;

-- 3.4 创建新的复合唯一索引（租户内唯一）
CREATE UNIQUE INDEX IF NOT EXISTS uk_tenant_menu_code
ON menu_permissions(tenant_id, menu_code);

-- 3.5 创建租户索引
CREATE INDEX IF NOT EXISTS idx_menu_tenant
ON menu_permissions(tenant_id);

-- 3.6 创建父菜单索引
CREATE INDEX IF NOT EXISTS idx_menu_parent
ON menu_permissions(parent_id);

-- 3.7 将现有菜单标记为系统级菜单
UPDATE menu_permissions
SET is_system = 1, tenant_id = NULL
WHERE tenant_id IS NULL;

-- ============================================================
-- 第四部分：数据完整性保护
-- ============================================================

-- 4.1 防止删除有角色关联的系统权限
DROP TRIGGER IF EXISTS prevent_system_perm_delete;
CREATE TRIGGER prevent_system_perm_delete
BEFORE DELETE ON api_permissions
FOR EACH ROW
WHEN OLD.is_system = 1
BEGIN
    SELECT RAISE(ABORT, '不能删除系统预置权限')
    WHERE EXISTS (
        SELECT 1 FROM role_api_permissions
        WHERE permission_id = OLD.id
    );
END;

-- 4.2 防止删除有角色关联的系统数据范围规则
DROP TRIGGER IF EXISTS prevent_system_scope_delete;
CREATE TRIGGER prevent_system_scope_delete
BEFORE DELETE ON data_scope_rules
FOR EACH ROW
WHEN OLD.is_system = 1
BEGIN
    SELECT RAISE(ABORT, '不能删除系统预置数据范围规则')
    WHERE EXISTS (
        SELECT 1 FROM role_data_scopes
        WHERE scope_rule_id = OLD.id
    );
END;

-- 4.3 防止删除有角色关联的系统菜单
DROP TRIGGER IF EXISTS prevent_system_menu_delete;
CREATE TRIGGER prevent_system_menu_delete
BEFORE DELETE ON menu_permissions
FOR EACH ROW
WHEN OLD.is_system = 1
BEGIN
    SELECT RAISE(ABORT, '不能删除系统预置菜单')
    WHERE EXISTS (
        SELECT 1 FROM role_menus
        WHERE menu_id = OLD.id
    );
END;

-- ============================================================
-- 第五部分：审计视图
-- ============================================================

-- 5.1 租户权限使用情况视图
DROP VIEW IF EXISTS v_tenant_permission_summary;
CREATE VIEW v_tenant_permission_summary AS
SELECT
    t.id AS tenant_id,
    t.tenant_code,
    t.tenant_name,
    COUNT(DISTINCT u.id) AS user_count,
    COUNT(DISTINCT r.id) AS role_count,
    COUNT(DISTINCT rap.permission_id) AS permission_count,
    COUNT(DISTINCT rm.menu_id) AS menu_count,
    t.max_users,
    t.max_roles,
    t.plan_type,
    t.status
FROM tenants t
LEFT JOIN users u ON u.tenant_id = t.id AND u.is_active = 1
LEFT JOIN roles r ON r.tenant_id = t.id AND r.is_active = 1
LEFT JOIN role_api_permissions rap ON rap.role_id = r.id
LEFT JOIN role_menus rm ON rm.role_id = r.id
GROUP BY t.id, t.tenant_code, t.tenant_name, t.max_users, t.max_roles, t.plan_type, t.status;

-- 5.2 角色权限继承链视图
DROP VIEW IF EXISTS v_role_permission_chain;
CREATE VIEW v_role_permission_chain AS
WITH RECURSIVE role_hierarchy AS (
    -- 基础：所有角色
    SELECT
        id,
        role_code,
        role_name,
        parent_id,
        inherit_permissions,
        tenant_id,
        0 AS level,
        role_code AS path
    FROM roles
    WHERE parent_id IS NULL

    UNION ALL

    -- 递归：子角色
    SELECT
        r.id,
        r.role_code,
        r.role_name,
        r.parent_id,
        r.inherit_permissions,
        r.tenant_id,
        rh.level + 1,
        rh.path || ' > ' || r.role_code
    FROM roles r
    INNER JOIN role_hierarchy rh ON r.parent_id = rh.id
)
SELECT * FROM role_hierarchy;

-- 5.3 租户自定义资源统计视图
DROP VIEW IF EXISTS v_tenant_custom_resources;
CREATE VIEW v_tenant_custom_resources AS
SELECT
    t.id AS tenant_id,
    t.tenant_code,
    t.tenant_name,
    (SELECT COUNT(*) FROM api_permissions ap WHERE ap.tenant_id = t.id) AS custom_permissions,
    (SELECT COUNT(*) FROM data_scope_rules dsr WHERE dsr.tenant_id = t.id) AS custom_scope_rules,
    (SELECT COUNT(*) FROM menu_permissions mp WHERE mp.tenant_id = t.id) AS custom_menus,
    t.plan_type
FROM tenants t;

-- ============================================================
-- 完成提示
-- ============================================================
-- 迁移完成！
--
-- 多租户隔离规则：
-- 1. tenant_id = NULL：系统级资源，所有租户共享
-- 2. tenant_id = N：租户自定义资源，仅该租户可见
--
-- 受影响的表：
-- - api_permissions：API权限（新增 tenant_id, is_system）
-- - data_scope_rules：数据范围规则（新增 tenant_id, is_system）
-- - menu_permissions：菜单权限（新增 tenant_id, is_system）
--
-- 使用方法：
-- sqlite3 data/app.db < migrations/20260127_permission_tenant_enhancement_sqlite.sql
