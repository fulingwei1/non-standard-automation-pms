-- ============================================================================
-- 用户会话管理表
-- 创建时间: 2026-02-14
-- 描述: 支持Token刷新、会话管理、设备绑定和安全增强
-- ============================================================================

-- 创建用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 用户信息
    user_id INT NOT NULL COMMENT '用户ID',
    
    -- Token信息
    access_token_jti VARCHAR(64) NOT NULL UNIQUE COMMENT 'Access Token的JTI（JWT ID）',
    refresh_token_jti VARCHAR(64) NOT NULL UNIQUE COMMENT 'Refresh Token的JTI',
    
    -- 设备信息
    device_id VARCHAR(128) COMMENT '设备唯一标识（客户端生成）',
    device_name VARCHAR(100) COMMENT '设备名称（如：Chrome on Windows）',
    device_type VARCHAR(50) COMMENT '设备类型：desktop/mobile/tablet',
    
    -- 网络信息
    ip_address VARCHAR(50) COMMENT '登录IP地址',
    location VARCHAR(200) COMMENT '地理位置（基于IP）',
    
    -- User-Agent信息
    user_agent TEXT COMMENT '浏览器User-Agent',
    browser VARCHAR(50) COMMENT '浏览器名称',
    os VARCHAR(50) COMMENT '操作系统',
    
    -- 会话状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '会话是否活跃',
    
    -- 时间信息
    login_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后活动时间',
    expires_at TIMESTAMP NOT NULL COMMENT '会话过期时间',
    logout_at TIMESTAMP NULL COMMENT '登出时间',
    
    -- 安全标记
    is_suspicious BOOLEAN DEFAULT FALSE COMMENT '是否为可疑登录（异地/异常设备）',
    risk_score INT DEFAULT 0 COMMENT '风险评分（0-100）',
    
    -- 审计字段
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_user_active (user_id, is_active),
    INDEX idx_user_sessions_access_jti (access_token_jti),
    INDEX idx_user_sessions_refresh_jti (refresh_token_jti),
    INDEX idx_user_sessions_expires_at (expires_at),
    INDEX idx_user_sessions_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';
