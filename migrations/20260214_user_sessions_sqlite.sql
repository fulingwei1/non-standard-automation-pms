-- ============================================================================
-- 用户会话管理表
-- 创建时间: 2026-02-14
-- 描述: 支持Token刷新、会话管理、设备绑定和安全增强
-- ============================================================================

-- 创建用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 用户信息
    user_id INTEGER NOT NULL,
    
    -- Token信息
    access_token_jti VARCHAR(64) NOT NULL UNIQUE,
    refresh_token_jti VARCHAR(64) NOT NULL UNIQUE,
    
    -- 设备信息
    device_id VARCHAR(128),
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    
    -- 网络信息
    ip_address VARCHAR(50),
    location VARCHAR(200),
    
    -- User-Agent信息
    user_agent TEXT,
    browser VARCHAR(50),
    os VARCHAR(50),
    
    -- 会话状态
    is_active BOOLEAN NOT NULL DEFAULT 1,
    
    -- 时间信息
    login_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    logout_at TIMESTAMP,
    
    -- 安全标记
    is_suspicious BOOLEAN DEFAULT 0,
    risk_score INTEGER DEFAULT 0,
    
    -- 审计字段
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_access_jti ON user_sessions(access_token_jti);
CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_jti ON user_sessions(refresh_token_jti);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);

-- 注释（SQLite不支持COMMENT，这里用注释记录）
-- user_id: 用户ID
-- access_token_jti: Access Token的JTI（JWT ID）
-- refresh_token_jti: Refresh Token的JTI
-- device_id: 设备唯一标识（客户端生成）
-- device_name: 设备名称（如：Chrome on Windows）
-- device_type: 设备类型：desktop/mobile/tablet
-- ip_address: 登录IP地址
-- location: 地理位置（基于IP）
-- user_agent: 浏览器User-Agent
-- browser: 浏览器名称
-- os: 操作系统
-- is_active: 会话是否活跃
-- login_at: 登录时间
-- last_activity_at: 最后活动时间
-- expires_at: 会话过期时间
-- logout_at: 登出时间
-- is_suspicious: 是否为可疑登录（异地/异常设备）
-- risk_score: 风险评分（0-100）
