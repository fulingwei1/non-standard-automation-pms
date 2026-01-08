-- ECN知识库功能扩展 - SQLite版本
-- 添加解决方案模板表

-- 创建ECN解决方案模板表
CREATE TABLE IF NOT EXISTS ecn_solution_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    template_category VARCHAR(50),
    ecn_type VARCHAR(20),
    root_cause_category VARCHAR(50),
    keywords TEXT,
    solution_description TEXT NOT NULL,
    solution_steps TEXT,
    required_resources TEXT,
    estimated_cost NUMERIC(14, 2),
    estimated_days INTEGER,
    success_rate NUMERIC(5, 2) DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    avg_cost_saving NUMERIC(14, 2),
    avg_time_saving INTEGER,
    source_ecn_id INTEGER,
    created_from VARCHAR(20) DEFAULT 'MANUAL',
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    verified_by INTEGER,
    verified_at DATETIME,
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_solution_template_type ON ecn_solution_templates(ecn_type);
CREATE INDEX IF NOT EXISTS idx_solution_template_category ON ecn_solution_templates(template_category);
CREATE INDEX IF NOT EXISTS idx_solution_template_active ON ecn_solution_templates(is_active);
