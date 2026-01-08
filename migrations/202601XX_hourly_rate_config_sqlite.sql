-- 时薪配置管理模块 - SQLite 迁移文件
-- 创建日期：2025-01-XX

-- ============================================
-- 时薪配置表
-- ============================================

CREATE TABLE IF NOT EXISTS hourly_rate_configs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    config_type         VARCHAR(20) NOT NULL,                          -- 配置类型：USER/ROLE/DEPT/DEFAULT
    user_id             INTEGER,                                         -- 用户ID（config_type=USER时使用）
    role_id             INTEGER,                                         -- 角色ID（config_type=ROLE时使用）
    dept_id             INTEGER,                                         -- 部门ID（config_type=DEPT时使用）
    hourly_rate         NUMERIC(10, 2) NOT NULL,                        -- 时薪（元/小时）
    effective_date      DATE,                                            -- 生效日期
    expiry_date         DATE,                                            -- 失效日期
    is_active           BOOLEAN DEFAULT 1,                              -- 是否启用
    remark              TEXT,                                            -- 备注
    created_by          INTEGER,                                         -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (dept_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_hourly_rate_type ON hourly_rate_configs(config_type);
CREATE INDEX idx_hourly_rate_user ON hourly_rate_configs(user_id);
CREATE INDEX idx_hourly_rate_role ON hourly_rate_configs(role_id);
CREATE INDEX idx_hourly_rate_dept ON hourly_rate_configs(dept_id);
CREATE INDEX idx_hourly_rate_active ON hourly_rate_configs(is_active);






