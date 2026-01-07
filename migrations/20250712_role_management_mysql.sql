-- ============================================
-- 角色管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 创建角色管理相关表结构
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 扩展现有 roles 表
-- ============================================

-- 添加新字段到 roles 表
ALTER TABLE roles
    ADD COLUMN role_type VARCHAR(20) DEFAULT 'BUSINESS' COMMENT '角色类型: SYSTEM/BUSINESS/PROJECT/CUSTOM',
    ADD COLUMN scope_type VARCHAR(20) DEFAULT 'GLOBAL' COMMENT '作用域: GLOBAL/DEPT/PROJECT',
    ADD COLUMN parent_role_id INT UNSIGNED NULL COMMENT '父角色ID',
    ADD COLUMN level INT DEFAULT 2 COMMENT '角色层级: 0最高',
    ADD COLUMN inherit_permissions TINYINT(1) DEFAULT 0 COMMENT '是否继承父角色权限',
    ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态: DRAFT/INACTIVE/ACTIVE/ARCHIVED',
    ADD COLUMN description TEXT COMMENT '角色描述',
    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 外键约束
ALTER TABLE roles ADD CONSTRAINT fk_roles_parent FOREIGN KEY (parent_role_id) REFERENCES roles(id) ON DELETE SET NULL;

-- 索引
CREATE INDEX idx_roles_parent ON roles(parent_role_id);
CREATE INDEX idx_roles_level ON roles(level);
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_roles_type ON roles(role_type);

-- ============================================
-- 2. 角色模板表
-- ============================================

CREATE TABLE IF NOT EXISTS role_templates (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(30) NOT NULL UNIQUE COMMENT '模板编码',
    template_name VARCHAR(50) NOT NULL COMMENT '模板名称',
    role_type VARCHAR(20) NOT NULL DEFAULT 'BUSINESS' COMMENT '角色类型',
    scope_type VARCHAR(20) DEFAULT 'GLOBAL' COMMENT '作用域类型',
    data_scope VARCHAR(20) DEFAULT 'PROJECT' COMMENT '数据范围',
    level INT DEFAULT 2 COMMENT '角色层级',
    description TEXT COMMENT '描述',
    permission_snapshot JSON COMMENT '权限快照',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_role_templates_code (template_code),
    INDEX idx_role_templates_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色模板表';

-- ============================================
-- 3. 模板权限关联表
-- ============================================

CREATE TABLE IF NOT EXISTS role_template_permissions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_id INT UNSIGNED NOT NULL COMMENT '模板ID',
    permission_id INT UNSIGNED NOT NULL COMMENT '权限ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_tpl_perm (template_id, permission_id),
    INDEX idx_tpl_perms_template (template_id),
    INDEX idx_tpl_perms_perm (permission_id),

    CONSTRAINT fk_tpl_perms_template FOREIGN KEY (template_id) REFERENCES role_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_tpl_perms_perm FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板权限关联表';

-- ============================================
-- 4. 用户角色分配表（扩展版）
-- ============================================

CREATE TABLE IF NOT EXISTS user_role_assignments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    role_id INT UNSIGNED NOT NULL COMMENT '角色ID',
    scope_type VARCHAR(20) DEFAULT 'GLOBAL' COMMENT '作用域类型: GLOBAL/DEPT/PROJECT',
    scope_id INT UNSIGNED NULL COMMENT '作用域ID（部门或项目）',
    assigned_by INT UNSIGNED NOT NULL COMMENT '分配人',
    approved_by INT UNSIGNED NULL COMMENT '审批人',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态: PENDING/ACTIVE/EXPIRED/REVOKED',
    effective_from DATETIME NULL COMMENT '生效时间',
    effective_until DATETIME NULL COMMENT '失效时间',
    assignment_reason TEXT COMMENT '分配原因',
    revoke_reason TEXT COMMENT '回收原因',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_assignments_user (user_id),
    INDEX idx_assignments_role (role_id),
    INDEX idx_assignments_status (status),
    INDEX idx_assignments_scope (scope_type, scope_id),
    INDEX idx_assignments_effective (effective_from, effective_until),

    CONSTRAINT fk_assignments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_assignments_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_assignments_assigned_by FOREIGN KEY (assigned_by) REFERENCES users(id),
    CONSTRAINT fk_assignments_approved_by FOREIGN KEY (approved_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色分配表';

-- ============================================
-- 5. 角色分配审批记录表
-- ============================================

CREATE TABLE IF NOT EXISTS role_assignment_approvals (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT UNSIGNED NOT NULL COMMENT '分配记录ID',
    approver_id INT UNSIGNED NOT NULL COMMENT '审批人ID',
    decision VARCHAR(20) NOT NULL COMMENT '决定: APPROVED/REJECTED',
    comment TEXT COMMENT '审批意见',
    decided_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '决定时间',

    INDEX idx_approvals_assignment (assignment_id),
    INDEX idx_approvals_approver (approver_id),
    INDEX idx_approvals_decision (decision),

    CONSTRAINT fk_approvals_assignment FOREIGN KEY (assignment_id) REFERENCES user_role_assignments(id) ON DELETE CASCADE,
    CONSTRAINT fk_approvals_approver FOREIGN KEY (approver_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色分配审批记录表';

-- ============================================
-- 6. 部门表（如果不存在）
-- ============================================

CREATE TABLE IF NOT EXISTS departments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(20) NOT NULL UNIQUE COMMENT '部门编码',
    dept_name VARCHAR(50) NOT NULL COMMENT '部门名称',
    parent_id INT UNSIGNED NULL COMMENT '上级部门ID',
    manager_id INT UNSIGNED NULL COMMENT '部门经理ID',
    level INT DEFAULT 1 COMMENT '部门层级',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_departments_parent (parent_id),
    INDEX idx_departments_active (is_active),

    CONSTRAINT fk_departments_parent FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL,
    CONSTRAINT fk_departments_manager FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- ============================================
-- 7. 部门默认角色配置表
-- ============================================

CREATE TABLE IF NOT EXISTS department_default_roles (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    department_id INT UNSIGNED NOT NULL COMMENT '部门ID',
    role_id INT UNSIGNED NOT NULL COMMENT '角色ID',
    is_primary TINYINT(1) DEFAULT 0 COMMENT '是否主要角色',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_dept_role (department_id, role_id),
    INDEX idx_dept_roles_dept (department_id),
    INDEX idx_dept_roles_role (role_id),

    CONSTRAINT fk_dept_roles_dept FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    CONSTRAINT fk_dept_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门默认角色表';

-- ============================================
-- 8. 部门角色管理员表
-- ============================================

CREATE TABLE IF NOT EXISTS department_role_admins (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    department_id INT UNSIGNED NOT NULL COMMENT '部门ID',
    user_id INT UNSIGNED NOT NULL COMMENT '管理员用户ID',
    can_assign_roles JSON COMMENT '可分配的角色ID列表',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_dept_admin (department_id, user_id),
    INDEX idx_dept_admins_dept (department_id),
    INDEX idx_dept_admins_user (user_id),

    CONSTRAINT fk_dept_admins_dept FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    CONSTRAINT fk_dept_admins_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门角色管理员表';

-- ============================================
-- 9. 角色互斥规则表
-- ============================================

CREATE TABLE IF NOT EXISTS role_exclusions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role_id_a INT UNSIGNED NOT NULL COMMENT '角色A',
    role_id_b INT UNSIGNED NOT NULL COMMENT '角色B',
    exclusion_type VARCHAR(20) DEFAULT 'MUTUAL' COMMENT '互斥类型: MUTUAL/ONE_WAY',
    reason TEXT COMMENT '互斥原因',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_exclusions_role_a (role_id_a),
    INDEX idx_exclusions_role_b (role_id_b),
    INDEX idx_exclusions_active (is_active),

    CONSTRAINT fk_exclusions_role_a FOREIGN KEY (role_id_a) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_exclusions_role_b FOREIGN KEY (role_id_b) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色互斥规则表';

-- ============================================
-- 10. 角色审计日志表
-- ============================================

CREATE TABLE IF NOT EXISTS role_audits (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型',
    operator_id INT UNSIGNED NOT NULL COMMENT '操作人ID',
    target_type VARCHAR(20) NOT NULL COMMENT '目标类型: ROLE/USER_ROLE/TEMPLATE',
    target_id INT UNSIGNED NOT NULL COMMENT '目标ID',
    old_value JSON COMMENT '变更前值',
    new_value JSON COMMENT '变更后值',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_role_audits_event (event_type),
    INDEX idx_role_audits_target (target_type, target_id),
    INDEX idx_role_audits_operator (operator_id),
    INDEX idx_role_audits_time (created_at),

    CONSTRAINT fk_role_audits_operator FOREIGN KEY (operator_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色审计日志表';

-- ============================================
-- 11. 视图：用户有效角色
-- ============================================

CREATE OR REPLACE VIEW v_user_active_roles AS
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
  AND (ura.effective_from IS NULL OR ura.effective_from <= NOW())
  AND (ura.effective_until IS NULL OR ura.effective_until > NOW());

-- ============================================
-- 12. 视图：角色层级树（使用递归CTE，MySQL 8.0+）
-- ============================================

CREATE OR REPLACE VIEW v_role_hierarchy AS
WITH RECURSIVE role_tree AS (
    -- 根节点（无父角色）
    SELECT
        id, role_code, role_name, role_type,
        parent_role_id, level, data_scope, status,
        CAST(role_code AS CHAR(500)) AS path,
        0 AS depth
    FROM roles
    WHERE parent_role_id IS NULL

    UNION ALL

    -- 子节点
    SELECT
        r.id, r.role_code, r.role_name, r.role_type,
        r.parent_role_id, r.level, r.data_scope, r.status,
        CONCAT(rt.path, ' > ', r.role_code) AS path,
        rt.depth + 1 AS depth
    FROM roles r
    JOIN role_tree rt ON r.parent_role_id = rt.id
)
SELECT * FROM role_tree;

-- ============================================
-- 完成
-- ============================================

SET FOREIGN_KEY_CHECKS = 1;
