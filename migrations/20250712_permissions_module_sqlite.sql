-- Permission management module migration (SQLite)
-- Targets: users/roles/permissions/user_roles/role_permissions/project_members/permission_audits

PRAGMA foreign_keys = ON;
BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    username VARCHAR(50) UNIQUE,
    auth_type VARCHAR(20) DEFAULT 'wechat',
    last_login_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(30) UNIQUE NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    data_scope VARCHAR(20) DEFAULT 'PROJECT',
    is_system BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perm_code VARCHAR(100) UNIQUE NOT NULL,
    perm_name VARCHAR(100),
    module VARCHAR(50),
    action VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- CREATE TABLE IF NOT EXISTS project_members (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     project_id INTEGER NOT NULL,
--     user_id INTEGER NOT NULL,
--     role_in_project VARCHAR(50),
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (project_id) REFERENCES projects(id),
--     FOREIGN KEY (user_id) REFERENCES users(id)
-- );

CREATE TABLE IF NOT EXISTS permission_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER NOT NULL,
    action VARCHAR(50),
    target_type VARCHAR(20),
    target_id INTEGER NOT NULL,
    detail TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_employee ON users(employee_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_perm ON role_permissions(permission_id);
-- CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id);
-- CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_permission_audits_operator ON permission_audits(operator_id);

-- Uniqueness guards
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_roles_unique ON user_roles(user_id, role_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_role_permissions_unique ON role_permissions(role_id, permission_id);
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_project_members_unique ON project_members(project_id, user_id);

COMMIT;
