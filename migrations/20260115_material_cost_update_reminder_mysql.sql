-- ============================================
-- 物料成本更新提醒模块 - MySQL 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加物料成本更新提醒表
-- ============================================

-- 物料成本更新提醒表
CREATE TABLE IF NOT EXISTS material_cost_update_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reminder_type VARCHAR(50) DEFAULT 'PERIODIC' COMMENT '提醒类型：PERIODIC（定期）/MANUAL（手动）',
    reminder_interval_days INT DEFAULT 30 COMMENT '提醒间隔（天），默认30天',
    last_reminder_date DATE COMMENT '最后提醒日期',
    next_reminder_date DATE COMMENT '下次提醒日期',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用提醒',
    material_type_filter VARCHAR(50) COMMENT '物料类型筛选（为空表示全部）',
    include_standard BOOLEAN DEFAULT TRUE COMMENT '包含标准件',
    include_non_standard BOOLEAN DEFAULT TRUE COMMENT '包含非标准件',
    notify_roles JSON COMMENT '通知角色列表（JSON数组）',
    notify_users JSON COMMENT '通知用户ID列表（JSON数组）',
    reminder_count INT DEFAULT 0 COMMENT '提醒次数',
    last_updated_by INT COMMENT '最后更新人ID',
    last_updated_at DATETIME COMMENT '最后更新时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (last_updated_by) REFERENCES users(id),
    INDEX idx_reminder_type (reminder_type),
    INDEX idx_next_reminder_date (next_reminder_date),
    INDEX idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料成本更新提醒表';

-- 初始化默认提醒配置（每月提醒一次）
INSERT INTO material_cost_update_reminders (
    reminder_type,
    reminder_interval_days,
    next_reminder_date,
    is_enabled,
    include_standard,
    include_non_standard,
    notify_roles,
    reminder_count
) VALUES (
    'PERIODIC',
    30,
    DATE_ADD(CURDATE(), INTERVAL 30 DAY),
    TRUE,
    TRUE,
    TRUE,
    JSON_ARRAY('procurement', 'procurement_manager', '采购工程师', '采购专员', '采购部经理'),
    0
) ON DUPLICATE KEY UPDATE reminder_type = reminder_type;
