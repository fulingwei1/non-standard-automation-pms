-- ============================================
-- 角色管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 创建角色管理相关表结构
-- ============================================

-- ============================================
-- 1. 扩展现有 roles 表
-- ============================================

-- 备份原表（如果需要）
-- CREATE TABLE roles_backup AS SELECT * FROM roles;

-- 添加新字段到 roles 表
ALTER TABLE roles ADD COLUMN role_type VARCHAR(20) DEFAULT 'BUSINESS';
ALTER TABLE roles ADD COLUMN scope_type VARCHAR(20) DEFAULT 'GLOBAL';
ALTER TABLE roles ADD COLUMN parent_role_id INTEGER REFERENCES roles(id);
ALTER TABLE roles ADD COLUMN level INTEGER DEFAULT 2;
ALTER TABLE roles ADD COLUMN inherit_permissions BOOLEAN DEFAULT FALSE;
ALTER TABLE roles ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE roles ADD COLUMN description TEXT;
ALTER TABLE roles ADD COLUMN updated_at DATETIME;

-- 角色表索引
CREATE INDEX IF NOT EXISTS idx_roles_parent ON roles(parent_role_id);
CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);
CREATE INDEX IF NOT EXISTS idx_roles_status ON roles(status);
CREATE INDEX IF NOT EXISTS idx_roles_type ON roles(role_type);

-- ============================================
-- 2. 角色模板表
-- ============================================

CREATE TABLE IF NOT EXISTS role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(30) UNIQUE NOT NULL,
    template_name VARCHAR(50) NOT NULL,
    role_type VARCHAR(20) NOT NULL DEFAULT 'BUSINESS',
    scope_type VARCHAR(20) DEFAULT 'GLOBAL',
    data_scope VARCHAR(20) DEFAULT 'PROJECT',
    level INTEGER DEFAULT 2,
    description TEXT,
    permission_snapshot TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_role_templates_code ON role_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_role_templates_active ON role_templates(is_active);

-- ============================================
-- 3. 模板权限关联表
-- ============================================

CREATE TABLE IF NOT EXISTS role_template_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (template_id) REFERENCES role_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tpl_perms_template ON role_template_permissions(template_id);
CREATE INDEX IF NOT EXISTS idx_tpl_perms_perm ON role_template_permissions(permission_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tpl_perms_unique ON role_template_permissions(template_id, permission_id);

-- ============================================
-- 4. 用户角色分配表（扩展版）
-- ============================================

CREATE TABLE IF NOT EXISTS user_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    scope_type VARCHAR(20) DEFAULT 'GLOBAL',
    scope_id INTEGER,
    assigned_by INTEGER NOT NULL,
    approved_by INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',
    effective_from DATETIME,
    effective_until DATETIME,
    assignment_reason TEXT,
    revoke_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

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
    assignment_id INTEGER NOT NULL,
    approver_id INTEGER NOT NULL,
    decision VARCHAR(20) NOT NULL,
    comment TEXT,
    decided_at DATETIME DEFAULT CURRENT_TIMESTAMP,

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
    dept_code VARCHAR(20) UNIQUE NOT NULL,
    dept_name VARCHAR(50) NOT NULL,
    parent_id INTEGER,
    manager_id INTEGER,
    level INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_id);
CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active);

-- ============================================
-- 7. 部门默认角色配置表
-- ============================================

CREATE TABLE IF NOT EXISTS department_default_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dept_roles_dept ON department_default_roles(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_roles_role ON department_default_roles(role_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dept_roles_unique ON department_default_roles(department_id, role_id);

-- ============================================
-- 8. 部门角色管理员表
-- ============================================

CREATE TABLE IF NOT EXISTS department_role_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    can_assign_roles TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dept_admins_dept ON department_role_admins(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_admins_user ON department_role_admins(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dept_admins_unique ON department_role_admins(department_id, user_id);

-- ============================================
-- 9. 角色互斥规则表
-- ============================================

CREATE TABLE IF NOT EXISTS role_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id_a INTEGER NOT NULL,
    role_id_b INTEGER NOT NULL,
    exclusion_type VARCHAR(20) DEFAULT 'MUTUAL',
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

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
    event_type VARCHAR(50) NOT NULL,
    operator_id INTEGER NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_role_audits_event ON role_audits(event_type);
CREATE INDEX IF NOT EXISTS idx_role_audits_target ON role_audits(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_role_audits_operator ON role_audits(operator_id);
CREATE INDEX IF NOT EXISTS idx_role_audits_time ON role_audits(created_at);

-- ============================================
-- 11. 视图：用户有效角色
-- ============================================

CREATE VIEW IF NOT EXISTS v_user_active_roles AS
SELECT
    ura.id AS assignment_id,
    ura.user_id,
    u.username,
    e.name AS employee_name,
    ura.role_id,
    r.role_code,
    r.role_name,
    r.role_type,
    r.data_scope,
    r.level AS role_level,
    ura.scope_type,
    ura.scope_id,
    ura.effective_from,
    ura.effective_until
FROM user_role_assignments ura
JOIN users u ON ura.user_id = u.id
JOIN employees e ON u.employee_id = e.id
JOIN roles r ON ura.role_id = r.id
WHERE ura.status = 'ACTIVE'
  AND r.status = 'ACTIVE'
  AND (ura.effective_from IS NULL OR ura.effective_from <= CURRENT_TIMESTAMP)
  AND (ura.effective_until IS NULL OR ura.effective_until > CURRENT_TIMESTAMP);

-- ============================================
-- 12. 视图：角色层级树
-- ============================================

CREATE VIEW IF NOT EXISTS v_role_hierarchy AS
WITH RECURSIVE role_tree AS (
    -- 根节点（无父角色）
    SELECT
        id, role_code, role_name, role_type,
        parent_role_id, level, data_scope, status,
        role_code AS path,
        0 AS depth
    FROM roles
    WHERE parent_role_id IS NULL

    UNION ALL

    -- 子节点
    SELECT
        r.id, r.role_code, r.role_name, r.role_type,
        r.parent_role_id, r.level, r.data_scope, r.status,
        rt.path || ' > ' || r.role_code AS path,
        rt.depth + 1 AS depth
    FROM roles r
    JOIN role_tree rt ON r.parent_role_id = rt.id
)
SELECT * FROM role_tree;

-- ============================================
-- 完成
-- ============================================
