-- 文化墙配置表
CREATE TABLE IF NOT EXISTS culture_wall_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE COMMENT '配置名称',
    description VARCHAR(500) COMMENT '配置描述',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认配置',
    content_types JSON COMMENT '内容类型配置',
    visible_roles JSON COMMENT '可见角色列表',
    play_settings JSON COMMENT '播放设置',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES user(id),
    INDEX idx_culture_wall_config_enabled (is_enabled),
    INDEX idx_culture_wall_config_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文化墙配置表';
