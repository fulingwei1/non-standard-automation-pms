-- ============================================================
-- 多租户 SaaS 架构迁移脚本 (SQLite)
-- 创建日期: 2026-01-26
-- 说明: 添加租户支持，实现数据隔离
-- ============================================================

-- 1. 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    plan_type VARCHAR(20) DEFAULT 'FREE',
    max_users INTEGER DEFAULT 5,
    max_roles INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 1,
    settings JSON,
    contact_name VARCHAR(100),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),
    expired_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建角色模板表
CREATE TABLE IF NOT EXISTS role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(50) NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    data_scope VARCHAR(20) DEFAULT 'OWN',
    nav_groups JSON,
    ui_config JSON,
    permission_codes JSON,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 为 users 表添加租户字段
ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE users ADD COLUMN is_tenant_admin BOOLEAN DEFAULT FALSE;

-- 4. 为 roles 表添加租户字段
ALTER TABLE roles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE roles ADD COLUMN source_template_id INTEGER REFERENCES role_templates(id);

-- 5. 创建默认租户（用于迁移现有数据）
INSERT INTO tenants (tenant_code, tenant_name, status, plan_type, max_users, max_roles, max_storage_gb)
VALUES ('DEFAULT', '默认租户', 'ACTIVE', 'ENTERPRISE', -1, -1, 100);

-- 6. 将现有用户关联到默认租户
UPDATE users SET tenant_id = (SELECT id FROM tenants WHERE tenant_code = 'DEFAULT') WHERE tenant_id IS NULL;

-- 7. 将现有角色关联到默认租户
UPDATE roles SET tenant_id = (SELECT id FROM tenants WHERE tenant_code = 'DEFAULT') WHERE tenant_id IS NULL;

-- 8. 复制现有角色到角色模板表
INSERT INTO role_templates (role_code, role_name, description, data_scope, nav_groups, ui_config, sort_order, is_active)
SELECT role_code, role_name, description, data_scope, nav_groups, ui_config, sort_order, is_active
FROM roles
WHERE is_system = TRUE OR role_code IN ('ADMIN', 'GM', 'PM', 'PMC', 'SALES_DIR', 'SA', 'PU_MGR', 'PU', 'ME', 'EE', 'QA');

-- 9. 添加租户管理员角色模板
INSERT INTO role_templates (role_code, role_name, description, data_scope, sort_order, is_active)
VALUES ('TENANT_ADMIN', '租户管理员', '租户内最高权限，可管理用户、角色和租户设置', 'ALL', 0, TRUE);

-- 10. 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_tenant_code ON tenants(tenant_code);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
