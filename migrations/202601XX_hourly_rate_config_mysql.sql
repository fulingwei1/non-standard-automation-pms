-- 时薪配置管理模块 - MySQL 迁移文件
-- 创建日期：2025-01-XX

-- ============================================
-- 时薪配置表
-- ============================================

CREATE TABLE IF NOT EXISTS hourly_rate_configs (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    config_type         VARCHAR(20) NOT NULL COMMENT '配置类型：USER/ROLE/DEPT/DEFAULT',
    user_id             BIGINT COMMENT '用户ID（config_type=USER时使用）',
    role_id             BIGINT COMMENT '角色ID（config_type=ROLE时使用）',
    dept_id             BIGINT COMMENT '部门ID（config_type=DEPT时使用）',
    hourly_rate         DECIMAL(10, 2) NOT NULL COMMENT '时薪（元/小时）',
    effective_date      DATE COMMENT '生效日期',
    expiry_date         DATE COMMENT '失效日期',
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    remark              TEXT COMMENT '备注',
    created_by          BIGINT COMMENT '创建人ID',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (dept_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    
    INDEX idx_hourly_rate_type (config_type),
    INDEX idx_hourly_rate_user (user_id),
    INDEX idx_hourly_rate_role (role_id),
    INDEX idx_hourly_rate_dept (dept_id),
    INDEX idx_hourly_rate_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='时薪配置表';






