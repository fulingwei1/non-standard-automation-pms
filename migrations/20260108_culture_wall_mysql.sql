-- ============================================================
-- 文化墙模块 DDL - MySQL 版本
-- 创建日期：2026-01-08
-- ============================================================

-- ==================== 文化墙内容 ====================

-- 文化墙内容表
CREATE TABLE IF NOT EXISTS culture_wall_content (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 内容类型
    content_type VARCHAR(30) NOT NULL COMMENT '内容类型:STRATEGY/CULTURE/IMPORTANT/NOTICE/REWARD',
    
    -- 内容信息
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT COMMENT '内容',
    summary VARCHAR(500) COMMENT '摘要',
    
    -- 媒体资源
    images JSON COMMENT '图片列表(JSON)',
    videos JSON COMMENT '视频列表(JSON)',
    attachments JSON COMMENT '附件列表(JSON)',
    
    -- 显示设置
    is_published TINYINT(1) DEFAULT 0 COMMENT '是否发布',
    publish_date DATE COMMENT '发布日期',
    expire_date DATE COMMENT '过期日期',
    priority INT DEFAULT 0 COMMENT '优先级',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    
    -- 阅读统计
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    
    -- 关联信息
    related_project_id BIGINT COMMENT '关联项目ID',
    related_department_id BIGINT COMMENT '关联部门ID',
    
    -- 发布人
    published_by BIGINT COMMENT '发布人ID',
    published_by_name VARCHAR(50) COMMENT '发布人姓名',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (related_project_id) REFERENCES project(id),
    FOREIGN KEY (related_department_id) REFERENCES organization(id),
    FOREIGN KEY (published_by) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    
    INDEX idx_culture_wall_type (content_type),
    INDEX idx_culture_wall_published (is_published, publish_date),
    INDEX idx_culture_wall_expire (expire_date)
) COMMENT '文化墙内容表';

-- ==================== 个人目标 ====================

-- 个人目标表
CREATE TABLE IF NOT EXISTS personal_goal (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    
    -- 目标信息
    goal_type VARCHAR(20) NOT NULL COMMENT '目标类型:MONTHLY/QUARTERLY/YEARLY',
    period VARCHAR(20) NOT NULL COMMENT '目标周期',
    title VARCHAR(200) NOT NULL COMMENT '目标标题',
    description TEXT COMMENT '目标描述',
    
    -- 目标指标
    target_value VARCHAR(50) COMMENT '目标值',
    current_value VARCHAR(50) COMMENT '当前值',
    unit VARCHAR(20) COMMENT '单位',
    
    -- 进度
    progress INT DEFAULT 0 COMMENT '进度百分比(0-100)',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'IN_PROGRESS' COMMENT '状态:IN_PROGRESS/COMPLETED/OVERDUE/CANCELLED',
    
    -- 时间
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    completed_date DATE COMMENT '完成日期',
    
    -- 备注
    notes TEXT COMMENT '备注',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    
    INDEX idx_personal_goal_user (user_id),
    INDEX idx_personal_goal_type_period (goal_type, period),
    INDEX idx_personal_goal_status (status)
) COMMENT '个人目标表';

-- ==================== 文化墙阅读记录 ====================

-- 文化墙阅读记录表
CREATE TABLE IF NOT EXISTS culture_wall_read_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    content_id BIGINT NOT NULL COMMENT '内容ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    
    -- 阅读时间
    read_at DATETIME NOT NULL COMMENT '阅读时间',
    
    -- 阅读时长(秒)
    read_duration INT DEFAULT 0 COMMENT '阅读时长(秒)',
    
    FOREIGN KEY (content_id) REFERENCES culture_wall_content(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id),
    
    UNIQUE KEY uk_read_record_content_user (content_id, user_id),
    INDEX idx_read_record_content (content_id),
    INDEX idx_read_record_user (user_id)
) COMMENT '文化墙阅读记录表';
