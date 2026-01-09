-- 报告配置表
CREATE TABLE IF NOT EXISTS meeting_report_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_name VARCHAR(200) NOT NULL COMMENT '配置名称',
    report_type VARCHAR(20) NOT NULL COMMENT '报告类型:ANNUAL/MONTHLY',
    description TEXT COMMENT '配置描述',
    enabled_metrics JSON COMMENT '启用的指标配置',
    comparison_config JSON COMMENT '对比配置',
    display_config JSON COMMENT '显示配置',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认配置',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES user(id),
    INDEX idx_report_config_type (report_type),
    INDEX idx_report_config_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会议报告配置表';

-- 报告指标定义表
CREATE TABLE IF NOT EXISTS report_metric_definition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_code VARCHAR(50) NOT NULL UNIQUE COMMENT '指标编码',
    metric_name VARCHAR(200) NOT NULL COMMENT '指标名称',
    category VARCHAR(50) NOT NULL COMMENT '指标分类',
    description TEXT COMMENT '指标说明',
    data_source VARCHAR(50) NOT NULL COMMENT '数据源表名',
    data_field VARCHAR(100) COMMENT '数据字段',
    filter_conditions JSON COMMENT '筛选条件(JSON)',
    calculation_type VARCHAR(20) NOT NULL COMMENT '计算类型:COUNT/SUM/AVG/MAX/MIN/RATIO/CUSTOM',
    calculation_formula TEXT COMMENT '计算公式（CUSTOM类型使用）',
    support_mom BOOLEAN DEFAULT TRUE COMMENT '支持环比',
    support_yoy BOOLEAN DEFAULT TRUE COMMENT '支持同比',
    unit VARCHAR(20) COMMENT '单位',
    format_type VARCHAR(20) DEFAULT 'NUMBER' COMMENT '格式类型:NUMBER/PERCENTAGE/CURRENCY',
    decimal_places INT DEFAULT 2 COMMENT '小数位数',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统预置',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES user(id),
    INDEX idx_metric_code (metric_code),
    INDEX idx_metric_category (category),
    INDEX idx_metric_source (data_source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告指标定义表';
