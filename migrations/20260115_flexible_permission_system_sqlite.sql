-- ============================================================
-- 灵活权限系统 - SQLite 迁移脚本
-- 创建时间: 2026-01-15
-- 说明: 支持自定义组织架构、岗位、职级、角色、权限
-- ============================================================

-- ========================================
-- 1. 组织单元表 (organization_units)
-- 支持 公司/事业部/部门/团队 的树形结构
-- ========================================
CREATE TABLE IF NOT EXISTS organization_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_code VARCHAR(50) UNIQUE NOT NULL,           -- 组织编码
    unit_name VARCHAR(100) NOT NULL,                 -- 组织名称
    unit_type VARCHAR(20) NOT NULL,                  -- 类型: COMPANY/BUSINESS_UNIT/DEPARTMENT/TEAM
    parent_id INTEGER,                               -- 上级组织ID
    manager_id INTEGER,                              -- 负责人ID (employee_id)
    level INTEGER DEFAULT 1,                         -- 层级深度
    path VARCHAR(500),                               -- 路径 (如: /1/3/5/)
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES organization_units(id)
);

CREATE INDEX IF NOT EXISTS idx_org_unit_type ON organization_units(unit_type);
CREATE INDEX IF NOT EXISTS idx_org_parent_id ON organization_units(parent_id);
CREATE INDEX IF NOT EXISTS idx_org_path ON organization_units(path);
CREATE INDEX IF NOT EXISTS idx_org_active ON organization_units(is_active);

-- ========================================
-- 2. 岗位表 (positions)
-- 公司自定义的岗位体系
-- ========================================
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_code VARCHAR(50) UNIQUE NOT NULL,       -- 岗位编码
    position_name VARCHAR(100) NOT NULL,             -- 岗位名称
    position_category VARCHAR(20) NOT NULL,          -- 类别: MANAGEMENT/TECHNICAL/SUPPORT/SALES/PRODUCTION
    org_unit_id INTEGER,                             -- 所属组织单元ID
    description TEXT,                                -- 岗位描述
    responsibilities TEXT,                           -- 岗位职责 (JSON)
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    sort_order INTEGER DEFAULT 0,                    -- 排序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id)
);

CREATE INDEX IF NOT EXISTS idx_position_category ON positions(position_category);
CREATE INDEX IF NOT EXISTS idx_position_org ON positions(org_unit_id);
CREATE INDEX IF NOT EXISTS idx_position_active ON positions(is_active);

-- ========================================
-- 3. 职级表 (job_levels)
-- 职级序列 (P序列/M序列/T序列)
-- ========================================
CREATE TABLE IF NOT EXISTS job_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_code VARCHAR(20) UNIQUE NOT NULL,          -- 职级编码 (如 P1-P10, M1-M5)
    level_name VARCHAR(50) NOT NULL,                 -- 职级名称
    level_category VARCHAR(10) NOT NULL,             -- 序列: P(专业)/M(管理)/T(技术)
    level_rank INTEGER NOT NULL,                     -- 职级数值 (用于比较)
    description TEXT,                                -- 职级描述
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    sort_order INTEGER DEFAULT 0,                    -- 排序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_level_rank ON job_levels(level_rank);
CREATE INDEX IF NOT EXISTS idx_level_category ON job_levels(level_category);

-- ========================================
-- 4. 员工组织分配表 (employee_org_assignments)
-- 支持一人多岗、矩阵式管理
-- ========================================
CREATE TABLE IF NOT EXISTS employee_org_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                    -- 员工ID
    org_unit_id INTEGER NOT NULL,                    -- 组织单元ID
    position_id INTEGER,                             -- 岗位ID
    job_level_id INTEGER,                            -- 职级ID
    is_primary BOOLEAN DEFAULT 1,                    -- 是否主要归属
    assignment_type VARCHAR(20) DEFAULT 'PERMANENT', -- 分配类型: PERMANENT/TEMPORARY/PROJECT
    start_date DATE,                                 -- 开始日期
    end_date DATE,                                   -- 结束日期
    is_active BOOLEAN DEFAULT 1,                     -- 是否有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id),
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (job_level_id) REFERENCES job_levels(id)
);

CREATE INDEX IF NOT EXISTS idx_eoa_employee ON employee_org_assignments(employee_id);
CREATE INDEX IF NOT EXISTS idx_eoa_org_unit ON employee_org_assignments(org_unit_id);
CREATE INDEX IF NOT EXISTS idx_eoa_position ON employee_org_assignments(position_id);
CREATE INDEX IF NOT EXISTS idx_eoa_primary ON employee_org_assignments(is_primary);
CREATE INDEX IF NOT EXISTS idx_eoa_active ON employee_org_assignments(is_active);
CREATE UNIQUE INDEX IF NOT EXISTS uk_eoa_emp_org_primary ON employee_org_assignments(employee_id, org_unit_id, is_primary);

-- ========================================
-- 5. 岗位默认角色表 (position_roles)
-- 岗位与系统角色的映射
-- ========================================
CREATE TABLE IF NOT EXISTS position_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,                    -- 岗位ID
    role_id INTEGER NOT NULL,                        -- 角色ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_position_role ON position_roles(position_id, role_id);
CREATE INDEX IF NOT EXISTS idx_pr_position ON position_roles(position_id);
CREATE INDEX IF NOT EXISTS idx_pr_role ON position_roles(role_id);

-- ========================================
-- 6. 数据权限规则表 (data_scope_rules)
-- 灵活的数据权限配置
-- ========================================
CREATE TABLE IF NOT EXISTS data_scope_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) UNIQUE NOT NULL,           -- 规则编码
    rule_name VARCHAR(100) NOT NULL,                 -- 规则名称
    scope_type VARCHAR(20) NOT NULL,                 -- 范围类型: ALL/BUSINESS_UNIT/DEPARTMENT/TEAM/PROJECT/OWN/CUSTOM
    scope_config TEXT,                               -- 范围配置 (JSON, 自定义规则时使用)
    description TEXT,                                -- 规则描述
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dsr_scope_type ON data_scope_rules(scope_type);
CREATE INDEX IF NOT EXISTS idx_dsr_active ON data_scope_rules(is_active);

-- ========================================
-- 7. 角色数据权限表 (role_data_scopes)
-- 角色对不同资源的数据权限
-- ========================================
CREATE TABLE IF NOT EXISTS role_data_scopes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,                        -- 角色ID
    resource_type VARCHAR(50) NOT NULL,              -- 资源类型 (project/customer/employee等)
    scope_rule_id INTEGER NOT NULL,                  -- 数据权限规则ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (scope_rule_id) REFERENCES data_scope_rules(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_role_resource ON role_data_scopes(role_id, resource_type);
CREATE INDEX IF NOT EXISTS idx_rds_role ON role_data_scopes(role_id);
CREATE INDEX IF NOT EXISTS idx_rds_resource ON role_data_scopes(resource_type);

-- ========================================
-- 8. 权限分组表 (permission_groups)
-- 权限的逻辑分组
-- ========================================
CREATE TABLE IF NOT EXISTS permission_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_code VARCHAR(50) UNIQUE NOT NULL,          -- 分组编码
    group_name VARCHAR(100) NOT NULL,                -- 分组名称
    parent_id INTEGER,                               -- 父分组ID
    description TEXT,                                -- 分组描述
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES permission_groups(id)
);

CREATE INDEX IF NOT EXISTS idx_pg_parent ON permission_groups(parent_id);

-- ========================================
-- 9. 菜单权限表 (menu_permissions)
-- 前端菜单和按钮配置
-- ========================================
CREATE TABLE IF NOT EXISTS menu_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_code VARCHAR(50) UNIQUE NOT NULL,           -- 菜单编码
    menu_name VARCHAR(100) NOT NULL,                 -- 菜单名称
    menu_path VARCHAR(200),                          -- 前端路由路径
    menu_icon VARCHAR(50),                           -- 菜单图标
    parent_id INTEGER,                               -- 父菜单ID
    menu_type VARCHAR(20) NOT NULL,                  -- 类型: DIRECTORY/MENU/BUTTON
    permission_id INTEGER,                           -- 关联的API权限ID (可选)
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_visible BOOLEAN DEFAULT 1,                    -- 是否可见
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES menu_permissions(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

CREATE INDEX IF NOT EXISTS idx_mp_parent ON menu_permissions(parent_id);
CREATE INDEX IF NOT EXISTS idx_mp_type ON menu_permissions(menu_type);
CREATE INDEX IF NOT EXISTS idx_mp_visible ON menu_permissions(is_visible);
CREATE INDEX IF NOT EXISTS idx_mp_active ON menu_permissions(is_active);

-- ========================================
-- 10. 角色菜单表 (role_menus)
-- 角色可访问的菜单
-- ========================================
CREATE TABLE IF NOT EXISTS role_menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,                        -- 角色ID
    menu_id INTEGER NOT NULL,                        -- 菜单ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (menu_id) REFERENCES menu_permissions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_role_menu ON role_menus(role_id, menu_id);
CREATE INDEX IF NOT EXISTS idx_rm_role ON role_menus(role_id);
CREATE INDEX IF NOT EXISTS idx_rm_menu ON role_menus(menu_id);

-- ========================================
-- 修改现有 roles 表
-- ========================================
-- 添加 role_type 字段 (SYSTEM/CUSTOM)
ALTER TABLE roles ADD COLUMN role_type VARCHAR(20) DEFAULT 'CUSTOM';

-- 添加 role_category 字段
ALTER TABLE roles ADD COLUMN role_category VARCHAR(50);

-- ========================================
-- 修改现有 permissions 表
-- ========================================
-- 添加 permission_type 字段 (API/MENU/BUTTON/DATA)
ALTER TABLE permissions ADD COLUMN permission_type VARCHAR(20) DEFAULT 'API';

-- 添加 group_id 字段
ALTER TABLE permissions ADD COLUMN group_id INTEGER REFERENCES permission_groups(id);

-- ========================================
-- 初始化数据: 职级
-- ========================================
INSERT OR IGNORE INTO job_levels (level_code, level_name, level_category, level_rank, description, sort_order) VALUES
-- P序列 (专业序列)
('P1', '助理', 'P', 1, '入门级专业人员', 1),
('P2', '初级专员', 'P', 2, '初级专业人员', 2),
('P3', '专员', 'P', 3, '独立工作的专业人员', 3),
('P4', '高级专员', 'P', 4, '高级专业人员', 4),
('P5', '资深专员', 'P', 5, '资深专业人员', 5),
('P6', '专家', 'P', 6, '领域专家', 6),
('P7', '高级专家', 'P', 7, '高级领域专家', 7),
('P8', '资深专家', 'P', 8, '资深领域专家', 8),
('P9', '首席专家', 'P', 9, '首席专家', 9),
('P10', '科学家/Fellow', 'P', 10, '顶级专家', 10),
-- M序列 (管理序列)
('M1', '主管', 'M', 11, '基层管理者', 11),
('M2', '经理', 'M', 12, '部门经理', 12),
('M3', '高级经理', 'M', 13, '高级经理', 13),
('M4', '总监', 'M', 14, '部门总监', 14),
('M5', '副总裁/VP', 'M', 15, '副总裁级别', 15),
('M6', '高级副总裁/SVP', 'M', 16, '高级副总裁', 16),
-- T序列 (技术序列)
('T1', '技术员', 'T', 1, '初级技术人员', 21),
('T2', '助理工程师', 'T', 2, '助理工程师', 22),
('T3', '工程师', 'T', 3, '工程师', 23),
('T4', '高级工程师', 'T', 4, '高级工程师', 24),
('T5', '资深工程师', 'T', 5, '资深工程师', 25),
('T6', '技术专家', 'T', 6, '技术专家', 26),
('T7', '高级技术专家', 'T', 7, '高级技术专家', 27),
('T8', '首席技术专家', 'T', 8, '首席技术专家', 28);

-- ========================================
-- 初始化数据: 数据权限规则
-- ========================================
INSERT OR IGNORE INTO data_scope_rules (rule_code, rule_name, scope_type, description) VALUES
('ALL', '全部数据', 'ALL', '可访问所有数据'),
('BUSINESS_UNIT', '本事业部数据', 'BUSINESS_UNIT', '可访问本事业部及下属组织的数据'),
('DEPARTMENT', '本部门数据', 'DEPARTMENT', '可访问本部门及下属团队的数据'),
('TEAM', '本团队数据', 'TEAM', '可访问本团队的数据'),
('PROJECT', '参与项目数据', 'PROJECT', '可访问参与的项目相关数据'),
('OWN', '仅个人数据', 'OWN', '仅可访问自己创建或负责的数据');

-- ========================================
-- 初始化数据: 权限分组
-- ========================================
INSERT OR IGNORE INTO permission_groups (group_code, group_name, description, sort_order) VALUES
('system', '系统管理', '系统管理相关权限', 1),
('org', '组织管理', '组织架构、岗位、职级管理', 2),
('project', '项目管理', '项目相关权限', 3),
('sales', '销售管理', '销售相关权限', 4),
('procurement', '采购管理', '采购相关权限', 5),
('production', '生产管理', '生产制造相关权限', 6),
('finance', '财务管理', '财务相关权限', 7),
('hr', '人力资源', '人力资源相关权限', 8),
('service', '售后服务', '售后服务相关权限', 9);

-- ========================================
-- 标记现有角色为系统角色
-- ========================================
UPDATE roles SET role_type = 'SYSTEM' WHERE role_type IS NULL OR role_type = '';

-- ============================================================
-- 迁移完成
-- ============================================================
