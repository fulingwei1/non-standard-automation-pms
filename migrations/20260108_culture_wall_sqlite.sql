-- ============================================================
-- 文化墙模块 DDL - SQLite 版本
-- 创建日期：2026-01-08
-- ============================================================

-- ==================== 文化墙内容 ====================

-- 文化墙内容表
CREATE TABLE IF NOT EXISTS culture_wall_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 内容类型
    content_type VARCHAR(30) NOT NULL,                    -- 内容类型:STRATEGY/CULTURE/IMPORTANT/NOTICE/REWARD
    
    -- 内容信息
    title VARCHAR(200) NOT NULL,                          -- 标题
    content TEXT,                                         -- 内容
    summary VARCHAR(500),                                 -- 摘要
    
    -- 媒体资源
    images TEXT,                                          -- 图片列表(JSON)
    videos TEXT,                                          -- 视频列表(JSON)
    attachments TEXT,                                     -- 附件列表(JSON)
    
    -- 显示设置
    is_published INTEGER DEFAULT 0,                       -- 是否发布
    publish_date DATE,                                    -- 发布日期
    expire_date DATE,                                     -- 过期日期
    priority INTEGER DEFAULT 0,                           -- 优先级
    display_order INTEGER DEFAULT 0,                      -- 显示顺序
    
    -- 阅读统计
    view_count INTEGER DEFAULT 0,                        -- 浏览次数
    
    -- 关联信息
    related_project_id INTEGER,                           -- 关联项目ID
    related_department_id INTEGER,                        -- 关联部门ID
    
    -- 发布人
    published_by INTEGER,                                 -- 发布人ID
    published_by_name VARCHAR(50),                        -- 发布人姓名
    
    created_by INTEGER,                                   -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (related_project_id) REFERENCES project(id),
    FOREIGN KEY (related_department_id) REFERENCES organization(id),
    FOREIGN KEY (published_by) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_culture_wall_type ON culture_wall_content(content_type);
CREATE INDEX IF NOT EXISTS idx_culture_wall_published ON culture_wall_content(is_published, publish_date);
CREATE INDEX IF NOT EXISTS idx_culture_wall_expire ON culture_wall_content(expire_date);

-- ==================== 个人目标 ====================

-- 个人目标表
CREATE TABLE IF NOT EXISTS personal_goal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                             -- 用户ID
    
    -- 目标信息
    goal_type VARCHAR(20) NOT NULL,                      -- 目标类型:MONTHLY/QUARTERLY/YEARLY
    period VARCHAR(20) NOT NULL,                          -- 目标周期
    title VARCHAR(200) NOT NULL,                          -- 目标标题
    description TEXT,                                     -- 目标描述
    
    -- 目标指标
    target_value VARCHAR(50),                             -- 目标值
    current_value VARCHAR(50),                            -- 当前值
    unit VARCHAR(20),                                    -- 单位
    
    -- 进度
    progress INTEGER DEFAULT 0,                          -- 进度百分比(0-100)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'IN_PROGRESS',            -- 状态:IN_PROGRESS/COMPLETED/OVERDUE/CANCELLED
    
    -- 时间
    start_date DATE,                                      -- 开始日期
    end_date DATE,                                       -- 结束日期
    completed_date DATE,                                  -- 完成日期
    
    -- 备注
    notes TEXT,                                           -- 备注
    
    created_by INTEGER,                                   -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_personal_goal_user ON personal_goal(user_id);
CREATE INDEX IF NOT EXISTS idx_personal_goal_type_period ON personal_goal(goal_type, period);
CREATE INDEX IF NOT EXISTS idx_personal_goal_status ON personal_goal(status);

-- ==================== 文化墙阅读记录 ====================

-- 文化墙阅读记录表
CREATE TABLE IF NOT EXISTS culture_wall_read_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,                          -- 内容ID
    user_id INTEGER NOT NULL,                             -- 用户ID
    
    -- 阅读时间
    read_at DATETIME NOT NULL,                            -- 阅读时间
    
    -- 阅读时长(秒)
    read_duration INTEGER DEFAULT 0,                      -- 阅读时长(秒)
    
    FOREIGN KEY (content_id) REFERENCES culture_wall_content(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id),
    UNIQUE(content_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_read_record_content ON culture_wall_read_record(content_id);
CREATE INDEX IF NOT EXISTS idx_read_record_user ON culture_wall_read_record(user_id);
