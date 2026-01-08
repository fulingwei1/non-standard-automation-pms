-- ============================================
-- 角色管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 创建角色管理相关表结构
-- ============================================

PRAGMA foreign_keys = ON;

-- ============================================
-- 1. 扩展现有 roles 表
-- ============================================

-- 添加新字段到 roles 表
ALTER TABLE roles ADD COLUMN role_type VARCHAR(20) DEFAULT 'BUSINESS'; -- 角色类型: SYSTEM/BUSINESS/PROJECT/CUSTOM
ALTER TABLE roles ADD COLUMN scope_type VARCHAR(20) DEFAULT 'GLOBAL'; -- 作用域: GLOBAL/DEPT/PROJECT
ALTER TABLE roles ADD COLUMN parent_role_id INTEGER NULL; -- 父角色ID
ALTER TABLE roles ADD COLUMN level INTEGER DEFAULT 2; -- 角色层级: 0最高
ALTER TABLE roles ADD COLUMN inherit_permissions INTEGER DEFAULT 0; -- 是否继承父角色权限
ALTER TABLE roles ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'; -- 状态: DRAFT/INACTIVE/ACTIVE/ARCHIVED
ALTER TABLE roles ADD COLUMN description TEXT; -- 角色描述
ALTER TABLE roles ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP; -- 更新时间

-- 索引
CREATE INDEX IF NOT EXISTS idx_roles_parent ON roles(parent_role_id);
CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);
CREATE INDEX IF NOT EXISTS idx_roles_status ON roles(status);
CREATE INDEX IF NOT EXISTS idx_roles_type ON roles(role_type);

-- ============================================
-- 2. 角色模板表
-- ============================================

CREATE TABLE IF NOT EXISTS role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(30) NOT NULL UNIQUE, -- 模板编码
    template_name VARCHAR(50) NOT NULL, -- 模板名称
    role_type VARCHAR(20) NOT NULL DEFAULT 'BUSINESS', -- 角色类型
    scope_type VARCHAR(20) DEFAULT 'GLOBAL', -- 作用域类型
    data_scope VARCHAR(20) DEFAULT 'PROJECT', -- 数据范围
    level INTEGER DEFAULT 2, -- 角色层级
    description TEXT, -- 描述
    permission_snapshot TEXT, -- 权限快照(JSON)
    is_active INTEGER DEFAULT 1, -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 更新时间
);

CREATE INDEX IF NOT EXISTS idx_role_templates_code ON role_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_role_templates_active ON role_templates(is_active);

-- ============================================
-- 3. 模板权限关联表
-- ============================================

CREATE TABLE IF NOT EXISTS role_template_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL, -- 模板ID
    permission_id INTEGER NOT NULL, -- 权限ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    UNIQUE(template_id, permission_id),
    FOREIGN KEY (template_id) REFERENCES role_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tpl_perms_template ON role_template_permissions(template_id);
CREATE INDEX IF NOT EXISTS idx_tpl_perms_perm ON role_template_permissions(permission_id);

-- ============================================
-- 4. 用户角色分配表（扩展版）
-- ============================================

CREATE TABLE IF NOT EXISTS user_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- 用户ID
    role_id INTEGER NOT NULL, -- 角色ID
    scope_type VARCHAR(20) DEFAULT 'GLOBAL', -- 作用域类型: GLOBAL/DEPT/PROJECT
    scope_id INTEGER NULL, -- 作用域ID（部门或项目）
    assigned_by INTEGER NOT NULL, -- 分配人
    approved_by INTEGER NULL, -- 审批人
    status VARCHAR(20) DEFAULT 'PENDING', -- 状态: PENDING/ACTIVE/EXPIRED/REVOKED
    effective_from DATETIME NULL, -- 生效时间
    effective_until DATETIME NULL, -- 失效时间
    assignment_reason TEXT, -- 分配原因
    revoke_reason TEXT, -- 回收原因
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_user ON user_role_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_role ON user_role_assignments(role_id);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON user_role_assignments(status);
CREATE INDEX IF NOT EXISTS idx_assignments_scope ON user_role_assignments(scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_assignments_effective ON user_role_assignments(effective_from, effective_until);

-- ============================================
-- 5. 角色分配审批记录表
-- ============================================

CREATE TABLE IF NOT EXISTS role_assignment_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL, -- 分配记录ID
    approver_id INTEGER NOT NULL, -- 审批人ID
    decision VARCHAR(20) NOT NULL, -- 决定: APPROVED/REJECTED
    comment TEXT, -- 审批意见
    decided_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 决定时间
    FOREIGN KEY (assignment_id) REFERENCES user_role_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_approvals_assignment ON role_assignment_approvals(assignment_id);
CREATE INDEX IF NOT EXISTS idx_approvals_approver ON role_assignment_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_approvals_decision ON role_assignment_approvals(decision);

-- ============================================
-- 6. 部门表（如果不存在）
-- ============================================

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code VARCHAR(20) NOT NULL UNIQUE, -- 部门编码
    dept_name VARCHAR(50) NOT NULL, -- 部门名称
    parent_id INTEGER NULL, -- 上级部门ID
    manager_id INTEGER NULL, -- 部门经理ID
    level INTEGER DEFAULT 1, -- 部门层级
    sort_order INTEGER DEFAULT 0, -- 排序
    is_active INTEGER DEFAULT 1, -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新时间
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_id);
CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active);

-- ============================================
-- 7. 部门默认角色配置表
-- ============================================

CREATE TABLE IF NOT EXISTS department_default_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL, -- 部门ID
    role_id INTEGER NOT NULL, -- 角色ID
    is_primary INTEGER DEFAULT 0, -- 是否主要角色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    UNIQUE(department_id, role_id),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dept_roles_dept ON department_default_roles(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_roles_role ON department_default_roles(role_id);

-- ============================================
-- 8. 部门角色管理员表
-- ============================================

CREATE TABLE IF NOT EXISTS department_role_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL, -- 部门ID
    user_id INTEGER NOT NULL, -- 管理员用户ID
    can_assign_roles TEXT, -- 可分配的角色ID列表(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    UNIQUE(department_id, user_id),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dept_admins_dept ON department_role_admins(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_admins_user ON department_role_admins(user_id);

-- ============================================
-- 9. 角色互斥规则表
-- ============================================

CREATE TABLE IF NOT EXISTS role_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id_a INTEGER NOT NULL, -- 角色A
    role_id_b INTEGER NOT NULL, -- 角色B
    exclusion_type VARCHAR(20) DEFAULT 'MUTUAL', -- 互斥类型: MUTUAL/ONE_WAY
    reason TEXT, -- 互斥原因
    is_active INTEGER DEFAULT 1, -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    FOREIGN KEY (role_id_a) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id_b) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exclusions_role_a ON role_exclusions(role_id_a);
CREATE INDEX IF NOT EXISTS idx_exclusions_role_b ON role_exclusions(role_id_b);
CREATE INDEX IF NOT EXISTS idx_exclusions_active ON role_exclusions(is_active);

-- ============================================
-- 10. 角色审计日志表
-- ============================================

CREATE TABLE IF NOT EXISTS role_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50) NOT NULL, -- 事件类型
    operator_id INTEGER NOT NULL, -- 操作人ID
    target_type VARCHAR(20) NOT NULL, -- 目标类型: ROLE/USER_ROLE/TEMPLATE
    target_id INTEGER NOT NULL, -- 目标ID
    old_value TEXT, -- 变更前值(JSON)
    new_value TEXT, -- 变更后值(JSON)
    ip_address VARCHAR(50), -- IP地址
    user_agent TEXT, -- 用户代理
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_role_audits_event ON role_audits(event_type);
CREATE INDEX IF NOT EXISTS idx_role_audits_target ON role_audits(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_role_audits_operator ON role_audits(operator_id);
CREATE INDEX IF NOT EXISTS idx_role_audits_time ON role_audits(created_at);





