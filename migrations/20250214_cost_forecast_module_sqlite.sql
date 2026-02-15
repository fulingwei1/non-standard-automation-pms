-- =====================================================
-- 成本预测和预警模块
-- 创建日期: 2025-02-14
-- 说明: 项目成本预测、趋势分析、成本预警功能
-- =====================================================

-- 1. 成本预测表
CREATE TABLE IF NOT EXISTS cost_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    
    -- 预测方法和时间
    forecast_method VARCHAR(50) NOT NULL DEFAULT 'LINEAR',
    forecast_date DATE NOT NULL,
    forecast_month VARCHAR(7),
    
    -- 预测结果
    forecasted_completion_cost DECIMAL(14, 2) NOT NULL,
    forecasted_completion_date DATE,
    
    -- 当前状态（预测时的数据）
    current_progress_pct DECIMAL(5, 2),
    current_actual_cost DECIMAL(14, 2),
    current_budget DECIMAL(14, 2),
    
    -- 月度预测数据（JSON）
    monthly_forecast_data TEXT,
    
    -- 趋势数据（JSON）
    trend_data TEXT,
    
    -- 预测准确率（回填）
    actual_completion_cost DECIMAL(14, 2),
    forecast_accuracy DECIMAL(5, 2),
    forecast_error DECIMAL(14, 2),
    forecast_error_pct DECIMAL(5, 2),
    
    -- 参数记录（JSON）
    parameters TEXT,
    
    -- 备注
    description TEXT,
    created_by INTEGER,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cost_forecast_project ON cost_forecasts(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_forecast_date ON cost_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_cost_forecast_month ON cost_forecasts(forecast_month);
CREATE INDEX IF NOT EXISTS idx_cost_forecast_method ON cost_forecasts(forecast_method);

-- 2. 成本预警表
CREATE TABLE IF NOT EXISTS cost_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    
    -- 预警类型和级别
    alert_type VARCHAR(50) NOT NULL,
    alert_level VARCHAR(20) NOT NULL DEFAULT 'WARNING',
    
    -- 预警时间
    alert_date DATE NOT NULL,
    alert_month VARCHAR(7),
    
    -- 预警数据
    current_cost DECIMAL(14, 2),
    budget_amount DECIMAL(14, 2),
    threshold DECIMAL(5, 2),
    current_progress DECIMAL(5, 2),
    cost_consumption_rate DECIMAL(5, 2),
    
    -- 预警详情
    alert_title VARCHAR(200) NOT NULL,
    alert_message TEXT NOT NULL,
    alert_data TEXT,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',
    acknowledged_by INTEGER,
    acknowledged_at DATETIME,
    resolved_at DATETIME,
    
    -- 处理信息
    resolution_note TEXT,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cost_alert_project ON cost_alerts(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_type ON cost_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_cost_alert_level ON cost_alerts(alert_level);
CREATE INDEX IF NOT EXISTS idx_cost_alert_date ON cost_alerts(alert_date);
CREATE INDEX IF NOT EXISTS idx_cost_alert_status ON cost_alerts(status);

-- 3. 成本预警规则表
CREATE TABLE IF NOT EXISTS cost_alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 规则名称和编码
    rule_name VARCHAR(200) NOT NULL,
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- 项目关联（NULL = 全局规则）
    project_id INTEGER,
    
    -- 规则类型
    alert_type VARCHAR(50) NOT NULL,
    
    -- 规则配置（JSON）
    rule_config TEXT NOT NULL,
    
    -- 是否启用
    is_enabled BOOLEAN DEFAULT 1,
    
    -- 优先级
    priority INTEGER DEFAULT 100,
    
    -- 通知配置
    notification_enabled BOOLEAN DEFAULT 1,
    notification_recipients TEXT,
    
    -- 描述
    description TEXT,
    
    -- 创建人
    created_by INTEGER,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cost_alert_rule_project ON cost_alert_rules(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_rule_type ON cost_alert_rules(alert_type);
CREATE INDEX IF NOT EXISTS idx_cost_alert_rule_enabled ON cost_alert_rules(is_enabled);

-- 4. 为 financial_project_costs 添加 cost_month 字段（如果不存在）
-- 此字段用于月度成本汇总和趋势分析
ALTER TABLE financial_project_costs ADD COLUMN cost_month VARCHAR(7);
CREATE INDEX IF NOT EXISTS idx_financial_cost_month_new ON financial_project_costs(cost_month);

-- 5. 插入默认预警规则
INSERT OR IGNORE INTO cost_alert_rules (rule_code, rule_name, alert_type, rule_config, description, priority)
VALUES 
    ('GLOBAL_OVERSPEND', '全局超支预警', 'OVERSPEND', '{"warning_threshold": 80, "critical_threshold": 100}', '当成本超过预算80%时发出警告，超过100%时发出严重警告', 10),
    ('GLOBAL_PROGRESS_MISMATCH', '全局进度不匹配预警', 'PROGRESS_MISMATCH', '{"deviation_threshold": 15}', '当成本消耗与进度偏差超过15%时发出预警', 20),
    ('GLOBAL_TREND_ANOMALY', '全局趋势异常预警', 'TREND_ANOMALY', '{"growth_rate_threshold": 0.3}', '当最近3个月平均成本增长率超过30%时发出预警', 30);

-- 完成
SELECT 'Cost forecast module migration completed successfully' AS status;
