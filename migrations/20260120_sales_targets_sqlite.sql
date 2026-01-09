-- 销售目标表 (SQLite)
-- 创建时间: 2026-01-20
-- 说明: Issue 6.5 - 销售目标管理功能

CREATE TABLE IF NOT EXISTS sales_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_scope VARCHAR(20) NOT NULL,
    user_id INTEGER,
    department_id INTEGER,
    team_id INTEGER,
    target_type VARCHAR(20) NOT NULL,
    target_period VARCHAR(20) NOT NULL,
    period_value VARCHAR(20) NOT NULL,
    target_value NUMERIC(14, 2) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sales_target_scope ON sales_targets(target_scope, user_id, department_id);
CREATE INDEX IF NOT EXISTS idx_sales_target_type_period ON sales_targets(target_type, target_period, period_value);
CREATE INDEX IF NOT EXISTS idx_sales_target_status ON sales_targets(status);
CREATE INDEX IF NOT EXISTS idx_sales_target_user ON sales_targets(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_target_department ON sales_targets(department_id);
