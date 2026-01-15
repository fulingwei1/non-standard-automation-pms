-- ============================================================
-- 灵活权限系统 - MySQL 迁移脚本
-- 创建时间: 2026-01-15
-- 说明: 支持自定义组织架构、岗位、职级、角色、权限
-- ============================================================

-- ========================================
-- 1. 组织单元表 (organization_units)
-- 支持 公司/事业部/部门/团队 的树形结构
-- ========================================
CREATE TABLE IF NOT EXISTS organization_units (
    id INT PRIMARY KEY AUTO_INCREMENT,
    unit_code VARCHAR(50) UNIQUE NOT NULL COMMENT '组织编码',
    unit_name VARCHAR(100) NOT NULL COMMENT '组织名称',
    unit_type ENUM('COMPANY', 'BUSINESS_UNIT', 'DEPARTMENT', 'TEAM') NOT NULL COMMENT '组织类型',
    parent_id INT COMMENT '上级组织ID',
    manager_id INT COMMENT '负责人ID(employee_id)',
    level INT DEFAULT 1 COMMENT '层级深度',
    path VARCHAR(500) COMMENT '路径(如: /1/3/5/)',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES organization_units(id) ON DELETE SET NULL,
    INDEX idx_unit_type (unit_type),
    INDEX idx_parent_id (parent_id),
    INDEX idx_path (path(255)),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织单元表';

-- ========================================
-- 2. 岗位表 (positions)
-- 公司自定义的岗位体系
-- ========================================
CREATE TABLE IF NOT EXISTS positions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    position_code VARCHAR(50) UNIQUE NOT NULL COMMENT '岗位编码',
    position_name VARCHAR(100) NOT NULL COMMENT '岗位名称',
    position_category ENUM('MANAGEMENT', 'TECHNICAL', 'SUPPORT', 'SALES', 'PRODUCTION') NOT NULL COMMENT '岗位类别',
    org_unit_id INT COMMENT '所属组织单元ID',
    description TEXT COMMENT '岗位描述',
    responsibilities JSON COMMENT '岗位职责',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
    INDEX idx_category (position_category),
    INDEX idx_org_unit (org_unit_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位表';

-- ========================================
-- 3. 职级表 (job_levels)
-- 职级序列 (P序列/M序列/T序列)
-- ========================================
CREATE TABLE IF NOT EXISTS job_levels (
    id INT PRIMARY KEY AUTO_INCREMENT,
    level_code VARCHAR(20) UNIQUE NOT NULL COMMENT '职级编码(如P1-P10, M1-M5)',
    level_name VARCHAR(50) NOT NULL COMMENT '职级名称',
    level_category ENUM('P', 'M', 'T') NOT NULL COMMENT '职级序列(P专业/M管理/T技术)',
    level_rank INT NOT NULL COMMENT '职级数值(用于比较)',
    description TEXT COMMENT '职级描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_rank (level_rank),
    INDEX idx_category (level_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='职级表';

-- ========================================
-- 4. 员工组织分配表 (employee_org_assignments)
-- 支持一人多岗、矩阵式管理
-- ========================================
CREATE TABLE IF NOT EXISTS employee_org_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL COMMENT '员工ID',
    org_unit_id INT NOT NULL COMMENT '组织单元ID',
    position_id INT COMMENT '岗位ID',
    job_level_id INT COMMENT '职级ID',
    is_primary BOOLEAN DEFAULT TRUE COMMENT '是否主要归属',
    assignment_type ENUM('PERMANENT', 'TEMPORARY', 'PROJECT') DEFAULT 'PERMANENT' COMMENT '分配类型',
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL,
    FOREIGN KEY (job_level_id) REFERENCES job_levels(id) ON DELETE SET NULL,
    INDEX idx_employee (employee_id),
    INDEX idx_org_unit (org_unit_id),
    INDEX idx_position (position_id),
    INDEX idx_primary (is_primary),
    INDEX idx_active (is_active),
    UNIQUE KEY uk_employee_org_primary (employee_id, org_unit_id, is_primary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='员工组织分配表';

-- ========================================
-- 5. 岗位默认角色表 (position_roles)
-- 岗位与系统角色的映射
-- ========================================
CREATE TABLE IF NOT EXISTS position_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    position_id INT NOT NULL COMMENT '岗位ID',
    role_id INT NOT NULL COMMENT '角色ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_position_role (position_id, role_id),
    INDEX idx_position (position_id),
    INDEX idx_role (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位默认角色映射表';

-- ========================================
-- 6. 数据权限规则表 (data_scope_rules)
-- 灵活的数据权限配置
-- ========================================
CREATE TABLE IF NOT EXISTS data_scope_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_code VARCHAR(50) UNIQUE NOT NULL COMMENT '规则编码',
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    scope_type ENUM('ALL', 'BUSINESS_UNIT', 'DEPARTMENT', 'TEAM', 'PROJECT', 'OWN', 'CUSTOM') NOT NULL COMMENT '范围类型',
    scope_config JSON COMMENT '范围配置(自定义规则时使用)',
    description TEXT COMMENT '规则描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_scope_type (scope_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据权限规则表';

-- ========================================
-- 7. 角色数据权限表 (role_data_scopes)
-- 角色对不同资源的数据权限
-- ========================================
CREATE TABLE IF NOT EXISTS role_data_scopes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL COMMENT '角色ID',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型(project/customer/employee等)',
    scope_rule_id INT NOT NULL COMMENT '数据权限规则ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (scope_rule_id) REFERENCES data_scope_rules(id) ON DELETE RESTRICT,
    UNIQUE KEY uk_role_resource (role_id, resource_type),
    INDEX idx_role (role_id),
    INDEX idx_resource (resource_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色数据权限关联表';

-- ========================================
-- 8. 权限分组表 (permission_groups)
-- 权限的逻辑分组
-- ========================================
CREATE TABLE IF NOT EXISTS permission_groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_code VARCHAR(50) UNIQUE NOT NULL COMMENT '分组编码',
    group_name VARCHAR(100) NOT NULL COMMENT '分组名称',
    parent_id INT COMMENT '父分组ID',
    description TEXT COMMENT '分组描述',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES permission_groups(id) ON DELETE SET NULL,
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限分组表';

-- ========================================
-- 9. 菜单权限表 (menu_permissions)
-- 前端菜单和按钮配置
-- ========================================
CREATE TABLE IF NOT EXISTS menu_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    menu_code VARCHAR(50) UNIQUE NOT NULL COMMENT '菜单编码',
    menu_name VARCHAR(100) NOT NULL COMMENT '菜单名称',
    menu_path VARCHAR(200) COMMENT '前端路由路径',
    menu_icon VARCHAR(50) COMMENT '菜单图标',
    parent_id INT COMMENT '父菜单ID',
    menu_type ENUM('DIRECTORY', 'MENU', 'BUTTON') NOT NULL COMMENT '菜单类型',
    permission_id INT COMMENT '关联的API权限ID(可选)',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_visible BOOLEAN DEFAULT TRUE COMMENT '是否可见',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES menu_permissions(id) ON DELETE SET NULL,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE SET NULL,
    INDEX idx_parent (parent_id),
    INDEX idx_menu_type (menu_type),
    INDEX idx_visible (is_visible),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜单权限表';

-- ========================================
-- 10. 角色菜单表 (role_menus)
-- 角色可访问的菜单
-- ========================================
CREATE TABLE IF NOT EXISTS role_menus (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL COMMENT '角色ID',
    menu_id INT NOT NULL COMMENT '菜单ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id) REFERENCES menu_permissions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_role_menu (role_id, menu_id),
    INDEX idx_role (role_id),
    INDEX idx_menu (menu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色菜单关联表';

-- ========================================
-- 修改现有 roles 表
-- ========================================
ALTER TABLE roles
    ADD COLUMN IF NOT EXISTS role_type ENUM('SYSTEM', 'CUSTOM') DEFAULT 'CUSTOM' COMMENT '角色类型(系统预置/自定义)',
    ADD COLUMN IF NOT EXISTS role_category VARCHAR(50) COMMENT '角色分类';

-- ========================================
-- 修改现有 permissions 表
-- ========================================
ALTER TABLE permissions
    ADD COLUMN IF NOT EXISTS permission_type ENUM('API', 'MENU', 'BUTTON', 'DATA') DEFAULT 'API' COMMENT '权限类型',
    ADD COLUMN IF NOT EXISTS group_id INT COMMENT '权限分组ID';

-- 添加外键约束
ALTER TABLE permissions
    ADD CONSTRAINT fk_permission_group FOREIGN KEY (group_id) REFERENCES permission_groups(id) ON DELETE SET NULL;

-- ========================================
-- 初始化数据: 职级
-- ========================================
INSERT IGNORE INTO job_levels (level_code, level_name, level_category, level_rank, description, sort_order) VALUES
-- P序列 (专业序列)
('P1', '助理', 'P', 1, '入门级专业人员', 1),
('P2', '初级专员', 'P', 2, '初级专业人员', 2),
('P3', '专员', 'P', 3, '独立工作的专业人员', 3),
('P4', '高级专员', 'P', 4, '高级专业人员', 4),
('P5', '资深专员', 'P', 5, '资深专业人员', 5),
('P6', '专家', 'P', 6, '领域专家', 6),
('P7', '���级专家', 'P', 7, '高级领域专家', 7),
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
-- 初���化数据: 数据权限规则
-- ========================================
INSERT IGNORE INTO data_scope_rules (rule_code, rule_name, scope_type, description) VALUES
('ALL', '全部数据', 'ALL', '可访问所有数据'),
('BUSINESS_UNIT', '本事业部数据', 'BUSINESS_UNIT', '可访问本事业部及下属组织的数据'),
('DEPARTMENT', '本部门数据', 'DEPARTMENT', '可访问本部门及下属团队的数据'),
('TEAM', '本团队数据', 'TEAM', '可访问本团队的数据'),
('PROJECT', '参与项目数据', 'PROJECT', '可访问参与的项目相关数据'),
('OWN', '仅个人数据', 'OWN', '仅可访问自己创建或负责的数据');

-- ========================================
-- 初始化数据: 权限分组
-- ========================================
INSERT IGNORE INTO permission_groups (group_code, group_name, description, sort_order) VALUES
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
