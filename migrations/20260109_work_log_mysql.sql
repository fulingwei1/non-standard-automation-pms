-- ============================================================
-- 工作日志模块 DDL - MySQL 版本
-- 创建日期：2026-01-09
-- ============================================================

-- ==================== 工作日志 ====================

-- 工作日志表
CREATE TABLE IF NOT EXISTS work_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 人员信息
    user_id BIGINT NOT NULL COMMENT '提交人ID',
    user_name VARCHAR(50) COMMENT '提交人姓名（冗余字段）',
    
    -- 工作信息
    work_date DATE NOT NULL COMMENT '工作日期',
    content TEXT NOT NULL COMMENT '工作内容（限制300字）',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/SUBMITTED',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_work_log_user (user_id),
    INDEX idx_work_log_date (work_date),
    INDEX idx_work_log_status (status),
    INDEX idx_work_log_user_date (user_id, work_date),
    UNIQUE KEY uq_work_log_user_date (user_id, work_date)
) COMMENT '工作日志表';

-- ==================== 工作日志配置 ====================

-- 工作日志配置表
CREATE TABLE IF NOT EXISTS work_log_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 适用范围
    user_id BIGINT COMMENT '用户ID（NULL表示全员）',
    department_id BIGINT COMMENT '部门ID（可选）',
    
    -- 配置项
    is_required TINYINT(1) DEFAULT 1 COMMENT '是否必须提交',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    remind_time VARCHAR(10) DEFAULT '18:00' COMMENT '提醒时间（HH:mm格式）',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    INDEX idx_work_log_config_user (user_id),
    INDEX idx_work_log_config_dept (department_id),
    INDEX idx_work_log_config_active (is_active)
) COMMENT '工作日志配置表';

-- ==================== 工作日志提及关联 ====================

-- 工作日志提及关联表
CREATE TABLE IF NOT EXISTS work_log_mentions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联工作日志
    work_log_id BIGINT NOT NULL COMMENT '工作日志ID',
    
    -- 提及信息
    mention_type VARCHAR(20) NOT NULL COMMENT '提及类型：PROJECT/MACHINE/USER',
    mention_id BIGINT NOT NULL COMMENT '被提及对象ID',
    mention_name VARCHAR(200) COMMENT '被提及对象名称（冗余字段）',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_log_id) REFERENCES work_logs(id) ON DELETE CASCADE,
    INDEX idx_work_log_mention_log (work_log_id),
    INDEX idx_work_log_mention_type (mention_type),
    INDEX idx_work_log_mention_id (mention_id),
    INDEX idx_work_log_mention_type_id (mention_type, mention_id)
) COMMENT '工作日志提及关联表';
