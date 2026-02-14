-- 创建 API 权限表
CREATE TABLE IF NOT EXISTS api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    perm_code VARCHAR(100) NOT NULL,
    perm_name VARCHAR(200) NOT NULL,
    module VARCHAR(50),
    page_code VARCHAR(50),
    action VARCHAR(20),
    description TEXT,
    permission_type VARCHAR(20) NOT NULL DEFAULT 'API',
    group_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_system BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants (id),
    CONSTRAINT uk_tenant_perm_code UNIQUE (tenant_id, perm_code)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_api_perm_tenant ON api_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_perm_module ON api_permissions(module);

-- 创建角色API权限关联表
CREATE TABLE IF NOT EXISTS role_api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles (id),
    FOREIGN KEY (permission_id) REFERENCES api_permissions (id),
    CONSTRAINT uk_role_api_permission UNIQUE (role_id, permission_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_rap_role ON role_api_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_rap_permission ON role_api_permissions(permission_id);
