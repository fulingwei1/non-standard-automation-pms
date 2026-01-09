-- 文化墙配置表
CREATE TABLE IF NOT EXISTS culture_wall_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    is_enabled BOOLEAN DEFAULT 1,
    is_default BOOLEAN DEFAULT 0,
    content_types TEXT,  -- JSON格式
    visible_roles TEXT,  -- JSON格式
    play_settings TEXT,  -- JSON格式
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_culture_wall_config_enabled ON culture_wall_config(is_enabled);
CREATE INDEX IF NOT EXISTS idx_culture_wall_config_default ON culture_wall_config(is_default);
