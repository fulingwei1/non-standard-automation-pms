-- ============================================
-- 预警订阅配置表 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-08
-- 说明: 用户预警订阅配置
-- ============================================

-- ============================================
-- 预警订阅配置表
-- ============================================

CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,                     -- 用户ID
    alert_type          VARCHAR(50),                          -- 预警类型（空表示全部）
    project_id          INTEGER,                              -- 项目ID（空表示全部）
    
    -- 订阅配置
    min_level           VARCHAR(20) DEFAULT 'WARNING',       -- 最低接收级别
    notify_channels     TEXT,                                 -- 通知渠道JSON: ["SYSTEM","EMAIL","WECHAT"]
    
    -- 免打扰时段
    quiet_start         VARCHAR(10),                         -- 免打扰开始时间（HH:mm格式）
    quiet_end           VARCHAR(10),                          -- 免打扰结束时间（HH:mm格式）
    
    -- 状态
    is_active           BOOLEAN DEFAULT 1,                   -- 是否启用
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_user ON alert_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_type ON alert_subscriptions(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_project ON alert_subscriptions(project_id);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_active ON alert_subscriptions(is_active);
