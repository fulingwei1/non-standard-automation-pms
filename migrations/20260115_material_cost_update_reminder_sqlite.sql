-- ============================================
-- 物料成本更新提醒模块 - SQLite 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加物料成本更新提醒表
-- ============================================

-- 物料成本更新提醒表
CREATE TABLE IF NOT EXISTS material_cost_update_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder_type VARCHAR(50) DEFAULT 'PERIODIC',
    reminder_interval_days INTEGER DEFAULT 30,
    last_reminder_date DATE,
    next_reminder_date DATE,
    is_enabled BOOLEAN DEFAULT 1,
    material_type_filter VARCHAR(50),
    include_standard BOOLEAN DEFAULT 1,
    include_non_standard BOOLEAN DEFAULT 1,
    notify_roles TEXT,
    notify_users TEXT,
    reminder_count INTEGER DEFAULT 0,
    last_updated_by INTEGER,
    last_updated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (last_updated_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_reminder_type ON material_cost_update_reminders(reminder_type);
CREATE INDEX IF NOT EXISTS idx_next_reminder_date ON material_cost_update_reminders(next_reminder_date);
CREATE INDEX IF NOT EXISTS idx_is_enabled ON material_cost_update_reminders(is_enabled);

-- 初始化默认提醒配置（每月提醒一次）
INSERT OR IGNORE INTO material_cost_update_reminders (
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
    date('now', '+30 days'),
    1,
    1,
    1,
    '["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"]',
    0
);
