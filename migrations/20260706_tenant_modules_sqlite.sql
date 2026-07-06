-- P1 立规：租户模块开通表。模块 key 权威清单在 app/modules/registry.py，
-- 闸门语义（grandfather/strict/off）见 app/services/tenant_module_service.py。
CREATE TABLE IF NOT EXISTS tenant_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    module_key VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    expires_at DATETIME,
    enabled_by INTEGER REFERENCES users(id),
    config JSON,
    created_at DATETIME,
    updated_at DATETIME,
    CONSTRAINT uq_tenant_module UNIQUE (tenant_id, module_key)
);
CREATE INDEX IF NOT EXISTS idx_tenant_modules_tenant ON tenant_modules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_modules_key ON tenant_modules(module_key);
