-- ============================================================
-- 矩阵式项目管理转型 - MySQL 版本
-- 创建日期：2026-01-20
-- 说明：支持项目文件夹/工作空间，整合奖金、会议、问题、文档
-- ============================================================

-- ==================== 1. 扩展 StrategicMeeting 表 ====================

ALTER TABLE strategic_meeting 
ADD COLUMN related_project_ids JSON COMMENT '关联项目ID列表（JSON数组，支持多项目关联）' AFTER project_id;

-- 注意：MySQL 5.7+ 支持 JSON 类型，但 JSON 数组查询需要使用 JSON_CONTAINS 函数
-- 索引创建可能需要根据实际使用的 MySQL 版本调整

-- ==================== 2. 扩展 ProjectMember 表 ====================

ALTER TABLE project_members
ADD COLUMN commitment_level VARCHAR(20) COMMENT '投入级别：FULL/PARTIAL/ADVISORY' AFTER end_date,
ADD COLUMN reporting_to_pm BOOLEAN DEFAULT TRUE COMMENT '是否向项目经理汇报' AFTER commitment_level,
ADD COLUMN dept_manager_notified BOOLEAN DEFAULT FALSE COMMENT '部门经理是否已通知' AFTER reporting_to_pm;

-- 添加索引
CREATE INDEX idx_project_members_commitment ON project_members(commitment_level);
CREATE INDEX idx_project_members_reporting ON project_members(reporting_to_pm);

-- ==================== 3. 创建 ProjectMemberContribution 表 ====================

CREATE TABLE IF NOT EXISTS project_member_contributions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL COMMENT '项目ID',
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    period VARCHAR(7) NOT NULL COMMENT '统计周期 YYYY-MM',
    
    -- 工作量指标
    task_count INT DEFAULT 0 COMMENT '完成任务数',
    task_hours DECIMAL(10,2) DEFAULT 0 COMMENT '任务工时',
    actual_hours DECIMAL(10,2) DEFAULT 0 COMMENT '实际投入工时',
    
    -- 质量指标
    deliverable_count INT DEFAULT 0 COMMENT '交付物数量',
    issue_count INT DEFAULT 0 COMMENT '问题数',
    issue_resolved INT DEFAULT 0 COMMENT '解决问题数',
    
    -- 贡献度评分
    contribution_score DECIMAL(5,2) COMMENT '贡献度评分',
    pm_rating INT COMMENT '项目经理评分 1-5',
    
    -- 奖金关联
    bonus_amount DECIMAL(14,2) DEFAULT 0 COMMENT '项目奖金金额',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_member_contrib (project_id, user_id, period),
    KEY idx_project_member_contrib_project (project_id),
    KEY idx_project_member_contrib_user (user_id),
    KEY idx_project_member_contrib_period (period),
    CONSTRAINT fk_project_member_contrib_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_project_member_contrib_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员贡献度表';

-- ==================== 4. 创建 SolutionTemplate 表 ====================

CREATE TABLE IF NOT EXISTS solution_templates (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    template_name VARCHAR(200) NOT NULL COMMENT '模板名称',
    template_code VARCHAR(50) UNIQUE COMMENT '模板编码',
    
    -- 关联信息
    issue_type VARCHAR(20) COMMENT '问题类型',
    category VARCHAR(20) COMMENT '问题分类',
    severity VARCHAR(20) COMMENT '严重程度',
    
    -- 解决方案内容
    solution TEXT NOT NULL COMMENT '解决方案模板',
    solution_steps JSON COMMENT '解决步骤（JSON数组）',
    
    -- 适用场景
    applicable_scenarios TEXT COMMENT '适用场景描述',
    prerequisites TEXT COMMENT '前置条件',
    precautions TEXT COMMENT '注意事项',
    
    -- 标签和分类
    tags JSON COMMENT '标签（JSON数组）',
    keywords JSON COMMENT '关键词（JSON数组，用于搜索）',
    
    -- 统计信息
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    success_rate DECIMAL(5,2) COMMENT '成功率（%）',
    avg_resolution_time DECIMAL(10,2) COMMENT '平均解决时间（小时）',
    
    -- 来源信息
    source_issue_id BIGINT COMMENT '来源问题ID（从哪个问题提取的模板）',
    created_by INT UNSIGNED COMMENT '创建人ID',
    created_by_name VARCHAR(50) COMMENT '创建人姓名',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开（所有项目可用）',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    KEY idx_solution_template_type (issue_type),
    KEY idx_solution_template_category (category),
    KEY idx_solution_template_code (template_code),
    KEY idx_solution_template_active (is_active),
    CONSTRAINT fk_solution_template_source FOREIGN KEY (source_issue_id) REFERENCES issues(id),
    CONSTRAINT fk_solution_template_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='解决方案模板表';
