-- 角色管理模块数据库迁移 (SQLite)
-- 日期: 2026-01-21
-- 描述: 扩展权限管理表结构，支持角色继承、数据权限规则、角色模板

-- 1. 扩展 roles 表 - 添加父角色ID（继承）
ALTER TABLE roles ADD COLUMN parent_id INTEGER REFERENCES roles(id);

-- 2. 扩展 permissions 表 - 添加页面编码和依赖权限
ALTER TABLE permissions ADD COLUMN page_code VARCHAR(50);
ALTER TABLE permissions ADD COLUMN depends_on INTEGER REFERENCES permissions(id);

-- 3. 创建数据权限自定义规则表
CREATE TABLE IF NOT EXISTS data_scope_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    rule_type VARCHAR(20) NOT NULL,  -- INCLUDE/EXCLUDE
    target_type VARCHAR(20) NOT NULL, -- DEPARTMENT/PROJECT/USER
    target_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_scope_rules_role ON data_scope_rules(role_id);
CREATE INDEX idx_data_scope_rules_target ON data_scope_rules(target_type, target_id);

-- 4. 创建角色模板表
CREATE TABLE IF NOT EXISTS role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    data_scope VARCHAR(20) DEFAULT 'OWN',
    permission_ids JSON,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. 插入预置角色模板
INSERT INTO role_templates (template_code, template_name, description, data_scope, permission_ids, sort_order) VALUES
('TPL_SALES_REP', '销售人员', '基础销售人员角色模板，可管理自己的线索、商机、报价', 'OWN', '[]', 1),
('TPL_SALES_MGR', '销售经理', '销售经理角色模板，可管理团队销售数据', 'SUBORDINATE', '[]', 2),
('TPL_SALES_DIR', '销售总监', '销售总监角色模板，可查看所有销售数据', 'ALL', '[]', 3),
('TPL_PM', '项目经理', '项目经理角色模板，可管理所属项目', 'PROJECT', '[]', 4),
('TPL_ENGINEER', '工程师', '工程师角色模板，可查看参与项目的任务', 'PROJECT', '[]', 5),
('TPL_FINANCE', '财务专员', '财务专员角色模板，可管理发票和收款', 'DEPT', '[]', 6),
('TPL_FINANCE_MGR', '财务经理', '财务经理角色模板，可查看所有财务数据', 'ALL', '[]', 7),
('TPL_PURCHASE', '采购专员', '采购专员角色模板，可管理采购订单', 'DEPT', '[]', 8),
('TPL_WAREHOUSE', '仓库管理员', '仓库管理员角色模板，可管理库存和收发货', 'DEPT', '[]', 9);

-- 6. 更新现有权限数据，补充 page_code（示例数据）
-- 销售模块
UPDATE permissions SET page_code = 'leads' WHERE module = 'SALES' AND perm_code LIKE '%LEAD%';
UPDATE permissions SET page_code = 'opportunities' WHERE module = 'SALES' AND perm_code LIKE '%OPP%';
UPDATE permissions SET page_code = 'quotes' WHERE module = 'SALES' AND perm_code LIKE '%QUOTE%';
UPDATE permissions SET page_code = 'contracts' WHERE module = 'SALES' AND perm_code LIKE '%CONTRACT%';
UPDATE permissions SET page_code = 'invoices' WHERE module = 'SALES' AND perm_code LIKE '%INVOICE%';

-- 项目模块
UPDATE permissions SET page_code = 'projects' WHERE module = 'PROJECT' AND perm_code LIKE '%PROJECT%';
UPDATE permissions SET page_code = 'tasks' WHERE module = 'PROJECT' AND perm_code LIKE '%TASK%';
UPDATE permissions SET page_code = 'milestones' WHERE module = 'PROJECT' AND perm_code LIKE '%MILESTONE%';

-- 系统模块
UPDATE permissions SET page_code = 'users' WHERE module = 'SYSTEM' AND perm_code LIKE '%USER%';
UPDATE permissions SET page_code = 'roles' WHERE module = 'SYSTEM' AND perm_code LIKE '%ROLE%';
UPDATE permissions SET page_code = 'permissions' WHERE module = 'SYSTEM' AND perm_code LIKE '%PERM%';
