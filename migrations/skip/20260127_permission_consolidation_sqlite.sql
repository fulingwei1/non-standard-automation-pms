-- ============================================================
-- 权限模型合并迁移脚本
-- 版本：20260127
-- 说明：拆分 permissions 表，统一数据权限架构
-- 决策：
--   1. 菜单权限的 perm_code 字段改为可选（支持纯目录节点）
--   2. Role.data_scope 仅迁移 project 资源类型
--   3. 迁移后立即删除旧表（激进模式）
-- ============================================================

PRAGMA foreign_keys = OFF;
BEGIN;

-- ============================================================
-- 步骤1：创建新的 api_permissions 表
-- ============================================================
CREATE TABLE IF NOT EXISTS api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perm_code VARCHAR(100) UNIQUE NOT NULL,
    perm_name VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    page_code VARCHAR(50),
    action VARCHAR(20),
    permission_type VARCHAR(20) DEFAULT 'API',
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_perm_code ON api_permissions(perm_code);
CREATE INDEX IF NOT EXISTS idx_api_perm_module ON api_permissions(module);
CREATE INDEX IF NOT EXISTS idx_api_perm_active ON api_permissions(is_active);

-- ============================================================
-- 步骤2：迁移现有 API 权限数据
-- ============================================================
INSERT INTO api_permissions (
    perm_code,
    perm_name,
    module,
    page_code,
    action,
    description,
    is_active,
    created_at,
    updated_at
)
SELECT
    perm_code,
    perm_name,
    module,
    page_code,
    action,
    description,
    COALESCE(is_active, 1),
    created_at,
    updated_at
FROM permissions
WHERE COALESCE(permission_type, 'API') = 'API';

-- ============================================================
-- 步骤3：重构 menu_permissions 表（移除外键，perm_code 改为可选）
-- ============================================================
-- 创建新表结构
CREATE TABLE IF NOT EXISTS menu_permissions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_code VARCHAR(50) UNIQUE NOT NULL,
    menu_name VARCHAR(100) NOT NULL,
    menu_path VARCHAR(200),
    menu_icon VARCHAR(50),
    parent_id INTEGER,
    menu_type VARCHAR(20) NOT NULL,
    perm_code VARCHAR(100),  -- 改为可选字符串引用，非外键
    sort_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES menu_permissions_new(id)
);

-- 迁移菜单数据
INSERT INTO menu_permissions_new (
    id,
    menu_code,
    menu_name,
    menu_path,
    menu_icon,
    parent_id,
    menu_type,
    perm_code,
    sort_order,
    is_visible,
    is_active,
    created_at,
    updated_at
)
SELECT
    mp.id,
    mp.menu_code,
    mp.menu_name,
    mp.menu_path,
    mp.menu_icon,
    mp.parent_id,
    mp.menu_type,
    p.perm_code,  -- 从关联的 permissions 表获取编码
    mp.sort_order,
    mp.is_visible,
    mp.is_active,
    mp.created_at,
    mp.updated_at
FROM menu_permissions mp
LEFT JOIN permissions p ON mp.permission_id = p.id;

-- 删除旧表并重命名新表
DROP TABLE menu_permissions;
ALTER TABLE menu_permissions_new RENAME TO menu_permissions;

-- 重建索引
CREATE INDEX IF NOT EXISTS idx_menu_code ON menu_permissions(menu_code);
CREATE INDEX IF NOT EXISTS idx_menu_parent ON menu_permissions(parent_id);
CREATE INDEX IF NOT EXISTS idx_menu_type ON menu_permissions(menu_type);
CREATE INDEX IF NOT EXISTS idx_menu_visible ON menu_permissions(is_visible);
CREATE INDEX IF NOT EXISTS idx_menu_active ON menu_permissions(is_active);

-- ============================================================
-- 步骤4：创建新的 role_api_permissions 表
-- ============================================================
CREATE TABLE IF NOT EXISTS role_api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES api_permissions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_role_api_perm ON role_api_permissions(role_id, permission_id);
CREATE INDEX IF NOT EXISTS idx_role_api_perm_role ON role_api_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_api_perm_perm ON role_api_permissions(permission_id);

-- 迁移角色API权限
INSERT INTO role_api_permissions (role_id, permission_id, created_at)
SELECT
    rp.role_id,
    ap.id,  -- 新的 api_permissions.id
    rp.created_at
FROM role_permissions rp
JOIN api_permissions ap ON rp.permission_id = ap.perm_code;

-- ============================================================
-- 步骤5：迁移 Role.data_scope 到 RoleDataScope（仅 project 资源）
-- ============================================================
INSERT INTO role_data_scopes (
    role_id,
    resource_type,
    scope_rule_id,
    is_active,
    created_at
)
SELECT
    r.id,
    'project' as resource_type,  -- 仅迁移项目资源
    (
        SELECT id FROM data_scope_rules
        WHERE rule_code = r.data_scope
        LIMIT 1
    ) as scope_rule_id,
    1 as is_active,
    CURRENT_TIMESTAMP
FROM roles r
WHERE r.data_scope IS NOT NULL
  AND r.data_scope != ''
  AND r.data_scope != 'PROJECT'  -- 跳过默认值
  AND EXISTS (SELECT 1 FROM data_scope_rules WHERE rule_code = r.data_scope);

-- ============================================================
-- 步骤6：删除旧表和字段（激进模式）
-- ============================================================

-- 删除旧的权限关联表
DROP TABLE IF EXISTS role_permissions;

-- 删除旧的 permissions 表
DROP TABLE IF EXISTS permissions;

-- 删除 roles 表的旧字段
ALTER TABLE roles DROP COLUMN IF EXISTS data_scope;

-- ============================================================
-- 步骤7：验证迁移结果
-- ============================================================

-- 验证1：API权限数据完整性
SELECT '=== API Permissions ===' as section;
SELECT 'Total count' as metric, COUNT(*) as value FROM api_permissions;

-- 验证2：菜单权限数据完整性
SELECT '=== Menu Permissions ===' as section;
SELECT
    'Total count' as metric,
    COUNT(*) as value
FROM menu_permissions;

SELECT
    'With perm_code' as metric,
    COUNT(*) as value
FROM menu_permissions
WHERE perm_code IS NOT NULL;

SELECT
    'Without perm_code (directories)' as metric,
    COUNT(*) as value
FROM menu_permissions
WHERE perm_code IS NULL;

-- 验证3：角色权限关联完整性
SELECT '=== Role Permissions ===' as section;
SELECT
    'Role-API permissions' as metric,
    COUNT(*) as value
FROM role_api_permissions;

SELECT
    'Role-Menus' as metric,
    COUNT(*) as value
FROM role_menus;

-- 验证4：数据权限迁移完整性
SELECT '=== Role Data Scopes ===' as section;
SELECT
    'Roles with new data scopes' as metric,
    COUNT(DISTINCT role_id) as value
FROM role_data_scopes;

-- 验证5：外键完整性
SELECT '=== Foreign Key Checks ===' as section;
SELECT
    'Broken menu parent references' as check_type,
    COUNT(*) as count
FROM menu_permissions
WHERE parent_id NOT IN (SELECT id FROM menu_permissions);

SELECT
    'Role-API permission orphaned roles' as check_type,
    COUNT(*) as count
FROM role_api_permissions rap
LEFT JOIN roles r ON rap.role_id = r.id
WHERE r.id IS NULL;

SELECT
    'Role-API permission orphaned permissions' as check_type,
    COUNT(*) as count
FROM role_api_permissions rap
LEFT JOIN api_permissions ap ON rap.permission_id = ap.id
WHERE ap.id IS NULL;

SELECT
    'Role-Menu orphaned roles' as check_type,
    COUNT(*) as count
FROM role_menus rm
LEFT JOIN roles r ON rm.role_id = r.id
WHERE r.id IS NULL;

SELECT
    'Role-Menu orphaned menus' as check_type,
    COUNT(*) as count
FROM role_menus rm
LEFT JOIN menu_permissions mp ON rm.menu_id = mp.id
WHERE mp.id IS NULL;

-- ============================================================
-- 迁移完成
-- ============================================================
COMMIT;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 迁移后清理建议
-- ============================================================
-- 1. 清空权限缓存（Redis）
--    FLUSHDB 或 DEL perm:*
--
-- 2. 重启应用服务
--
-- 3. 验证功能：
--    - 用户登录正常
--    - 权限检查工作
--    - 菜单树显示正确
--    - 数据权限过滤正确
--
-- 4. 监控错误日志 24 小时
--
-- ============================================================
