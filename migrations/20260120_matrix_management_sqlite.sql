-- ============================================================
-- 矩阵式项目管理转型 - SQLite 版本
-- 创建日期：2026-01-20
-- 说明：支持项目文件夹/工作空间，整合奖金、会议、问题、文档
-- ============================================================

-- ==================== 1. 扩展 StrategicMeeting 表 ====================

ALTER TABLE strategic_meeting 
ADD COLUMN related_project_ids TEXT;

-- ==================== 2. 扩展 ProjectMember 表 ====================

ALTER TABLE project_members
ADD COLUMN commitment_level VARCHAR(20);

ALTER TABLE project_members
ADD COLUMN reporting_to_pm BOOLEAN DEFAULT 1;

ALTER TABLE project_members
ADD COLUMN dept_manager_notified BOOLEAN DEFAULT 0;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_project_members_commitment ON project_members(commitment_level);
CREATE INDEX IF NOT EXISTS idx_project_members_reporting ON project_members(reporting_to_pm);

-- ==================== 3. 创建 ProjectMemberContribution 表 ====================

CREATE TABLE IF NOT EXISTS project_member_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                     -- 项目ID
    user_id INTEGER NOT NULL,                         -- 用户ID
    period VARCHAR(7) NOT NULL,                      -- 统计周期 YYYY-MM
    
    -- 工作量指标
    task_count INTEGER DEFAULT 0,                    -- 完成任务数
    task_hours DECIMAL(10,2) DEFAULT 0,              -- 任务工时
    actual_hours DECIMAL(10,2) DEFAULT 0,            -- 实际投入工时
    
    -- 质量指标
    deliverable_count INTEGER DEFAULT 0,              -- 交付物数量
    issue_count INTEGER DEFAULT 0,                   -- 问题数
    issue_resolved INTEGER DEFAULT 0,                 -- 解决问题数
    
    -- 贡献度评分
    contribution_score DECIMAL(5,2),                 -- 贡献度评分
    pm_rating INTEGER,                               -- 项目经理评分 1-5
    
    -- 奖金关联
    bonus_amount DECIMAL(14,2) DEFAULT 0,           -- 项目奖金金额
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(project_id, user_id, period)
);

CREATE INDEX IF NOT EXISTS idx_project_member_contrib_project ON project_member_contributions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_member_contrib_user ON project_member_contributions(user_id);
CREATE INDEX IF NOT EXISTS idx_project_member_contrib_period ON project_member_contributions(period);

-- ==================== 4. 创建 SolutionTemplate 表 ====================

CREATE TABLE IF NOT EXISTS solution_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name VARCHAR(200) NOT NULL,             -- 模板名称
    template_code VARCHAR(50) UNIQUE,                -- 模板编码
    
    -- 关联信息
    issue_type VARCHAR(20),                          -- 问题类型
    category VARCHAR(20),                            -- 问题分类
    severity VARCHAR(20),                            -- 严重程度
    
    -- 解决方案内容
    solution TEXT NOT NULL,                          -- 解决方案模板
    solution_steps TEXT,                             -- 解决步骤（JSON数组）
    
    -- 适用场景
    applicable_scenarios TEXT,                      -- 适用场景描述
    prerequisites TEXT,                             -- 前置条件
    precautions TEXT,                                -- 注意事项
    
    -- 标签和分类
    tags TEXT,                                       -- 标签（JSON数组）
    keywords TEXT,                                   -- 关键词（JSON数组，用于搜索）
    
    -- 统计信息
    usage_count INTEGER DEFAULT 0,                   -- 使用次数
    success_rate DECIMAL(5,2),                      -- 成功率（%）
    avg_resolution_time DECIMAL(10,2),               -- 平均解决时间（小时）
    
    -- 来源信息
    source_issue_id INTEGER,                         -- 来源问题ID
    created_by INTEGER,                              -- 创建人ID
    created_by_name VARCHAR(50),                     -- 创建人姓名
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    is_public BOOLEAN DEFAULT 1,                    -- 是否公开（所有项目可用）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_issue_id) REFERENCES issues(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_solution_template_type ON solution_templates(issue_type);
CREATE INDEX IF NOT EXISTS idx_solution_template_category ON solution_templates(category);
CREATE INDEX IF NOT EXISTS idx_solution_template_code ON solution_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_solution_template_active ON solution_templates(is_active);
