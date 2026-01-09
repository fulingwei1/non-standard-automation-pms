-- 报告配置表
CREATE TABLE IF NOT EXISTS meeting_report_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name VARCHAR(200) NOT NULL,
    report_type VARCHAR(20) NOT NULL,
    description TEXT,
    enabled_metrics TEXT,
    comparison_config TEXT,
    display_config TEXT,
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_report_config_type ON meeting_report_config(report_type);
CREATE INDEX IF NOT EXISTS idx_report_config_default ON meeting_report_config(is_default);

-- 报告指标定义表
CREATE TABLE IF NOT EXISTS report_metric_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_code VARCHAR(50) NOT NULL UNIQUE,
    metric_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    data_source VARCHAR(50) NOT NULL,
    data_field VARCHAR(100),
    filter_conditions TEXT,
    calculation_type VARCHAR(20) NOT NULL,
    calculation_formula TEXT,
    support_mom BOOLEAN DEFAULT 1,
    support_yoy BOOLEAN DEFAULT 1,
    unit VARCHAR(20),
    format_type VARCHAR(20) DEFAULT 'NUMBER',
    decimal_places INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT 1,
    is_system BOOLEAN DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_metric_code ON report_metric_definition(metric_code);
CREATE INDEX IF NOT EXISTS idx_metric_category ON report_metric_definition(category);
CREATE INDEX IF NOT EXISTS idx_metric_source ON report_metric_definition(data_source);
