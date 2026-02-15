-- =====================================================
-- 成本预测和预警模块（MySQL版本）
-- 创建日期: 2025-02-14
-- 说明: 项目成本预测、趋势分析、成本预警功能
-- =====================================================

-- 1. 成本预测表
CREATE TABLE IF NOT EXISTS cost_forecasts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    project_id INT NOT NULL COMMENT '项目ID',
    project_code VARCHAR(50) COMMENT '项目编号（冗余）',
    project_name VARCHAR(200) COMMENT '项目名称（冗余）',
    
    -- 预测方法和时间
    forecast_method VARCHAR(50) NOT NULL DEFAULT 'LINEAR' COMMENT '预测方法：LINEAR/EXPONENTIAL/HISTORICAL_AVERAGE',
    forecast_date DATE NOT NULL COMMENT '预测日期（预测时的日期）',
    forecast_month VARCHAR(7) COMMENT '预测月份(YYYY-MM)',
    
    -- 预测结果
    forecasted_completion_cost DECIMAL(14, 2) NOT NULL COMMENT '预测完工成本',
    forecasted_completion_date DATE COMMENT '预测完工日期',
    
    -- 当前状态（预测时的数据）
    current_progress_pct DECIMAL(5, 2) COMMENT '当前完成进度(%)',
    current_actual_cost DECIMAL(14, 2) COMMENT '当前实际成本',
    current_budget DECIMAL(14, 2) COMMENT '当前预算金额',
    
    -- 月度预测数据（JSON）
    monthly_forecast_data JSON COMMENT '月度预测数据',
    
    -- 趋势数据（JSON）
    trend_data JSON COMMENT '趋势数据',
    
    -- 预测准确率（回填）
    actual_completion_cost DECIMAL(14, 2) COMMENT '实际完工成本（用于验证）',
    forecast_accuracy DECIMAL(5, 2) COMMENT '预测准确率(%)',
    forecast_error DECIMAL(14, 2) COMMENT '预测误差（实际-预测）',
    forecast_error_pct DECIMAL(5, 2) COMMENT '预测误差率(%)',
    
    -- 参数记录（JSON）
    parameters JSON COMMENT '预测参数',
    
    -- 备注
    description TEXT COMMENT '预测说明',
    created_by INT COMMENT '创建人',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- 索引
    INDEX idx_cost_forecast_project (project_id),
    INDEX idx_cost_forecast_date (forecast_date),
    INDEX idx_cost_forecast_month (forecast_month),
    INDEX idx_cost_forecast_method (forecast_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本预测表';

-- 2. 成本预警表
CREATE TABLE IF NOT EXISTS cost_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    project_id INT NOT NULL COMMENT '项目ID',
    project_code VARCHAR(50) COMMENT '项目编号（冗余）',
    project_name VARCHAR(200) COMMENT '项目名称（冗余）',
    
    -- 预警类型和级别
    alert_type VARCHAR(50) NOT NULL COMMENT '预警类型：OVERSPEND/PROGRESS_MISMATCH/TREND_ANOMALY',
    alert_level VARCHAR(20) NOT NULL DEFAULT 'WARNING' COMMENT '预警级别：INFO/WARNING/CRITICAL',
    
    -- 预警时间
    alert_date DATE NOT NULL COMMENT '预警日期',
    alert_month VARCHAR(7) COMMENT '预警月份(YYYY-MM)',
    
    -- 预警数据
    current_cost DECIMAL(14, 2) COMMENT '当前实际成本',
    budget_amount DECIMAL(14, 2) COMMENT '预算金额',
    threshold DECIMAL(5, 2) COMMENT '阈值(%)',
    current_progress DECIMAL(5, 2) COMMENT '当前进度(%)',
    cost_consumption_rate DECIMAL(5, 2) COMMENT '成本消耗率(%)',
    
    -- 预警详情
    alert_title VARCHAR(200) NOT NULL COMMENT '预警标题',
    alert_message TEXT NOT NULL COMMENT '预警消息',
    alert_data JSON COMMENT '预警详细数据',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE/ACKNOWLEDGED/RESOLVED/IGNORED',
    acknowledged_by INT COMMENT '确认人ID',
    acknowledged_at DATETIME COMMENT '确认时间',
    resolved_at DATETIME COMMENT '解决时间',
    
    -- 处理信息
    resolution_note TEXT COMMENT '处理说明',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- 索引
    INDEX idx_cost_alert_project (project_id),
    INDEX idx_cost_alert_type (alert_type),
    INDEX idx_cost_alert_level (alert_level),
    INDEX idx_cost_alert_date (alert_date),
    INDEX idx_cost_alert_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本预警表';

-- 3. 成本预警规则表
CREATE TABLE IF NOT EXISTS cost_alert_rules (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    -- 规则名称和编码
    rule_name VARCHAR(200) NOT NULL COMMENT '规则名称',
    rule_code VARCHAR(50) UNIQUE NOT NULL COMMENT '规则编码',
    
    -- 项目关联（NULL = 全局规则）
    project_id INT COMMENT '项目ID（空=全局规则）',
    
    -- 规则类型
    alert_type VARCHAR(50) NOT NULL COMMENT '预警类型',
    
    -- 规则配置（JSON）
    rule_config JSON NOT NULL COMMENT '规则配置',
    
    -- 是否启用
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    -- 优先级
    priority INT DEFAULT 100 COMMENT '优先级',
    
    -- 通知配置
    notification_enabled BOOLEAN DEFAULT TRUE COMMENT '是否发送通知',
    notification_recipients JSON COMMENT '通知接收人列表',
    
    -- 描述
    description TEXT COMMENT '规则描述',
    
    -- 创建人
    created_by INT COMMENT '创建人',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- 索引
    INDEX idx_cost_alert_rule_project (project_id),
    INDEX idx_cost_alert_rule_type (alert_type),
    INDEX idx_cost_alert_rule_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本预警规则表';

-- 4. 为 financial_project_costs 添加 cost_month 字段（如果不存在）
ALTER TABLE financial_project_costs 
ADD COLUMN IF NOT EXISTS cost_month VARCHAR(7) COMMENT '成本月份(YYYY-MM)';

CREATE INDEX IF NOT EXISTS idx_financial_cost_month_new ON financial_project_costs(cost_month);

-- 5. 插入默认预警规则
INSERT INTO cost_alert_rules (rule_code, rule_name, alert_type, rule_config, description, priority)
VALUES 
    ('GLOBAL_OVERSPEND', '全局超支预警', 'OVERSPEND', '{"warning_threshold": 80, "critical_threshold": 100}', '当成本超过预算80%时发出警告，超过100%时发出严重警告', 10),
    ('GLOBAL_PROGRESS_MISMATCH', '全局进度不匹配预警', 'PROGRESS_MISMATCH', '{"deviation_threshold": 15}', '当成本消耗与进度偏差超过15%时发出预警', 20),
    ('GLOBAL_TREND_ANOMALY', '全局趋势异常预警', 'TREND_ANOMALY', '{"growth_rate_threshold": 0.3}', '当最近3个月平均成本增长率超过30%时发出预警', 30)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 完成
SELECT 'Cost forecast module migration completed successfully' AS status;
