-- AI项目规划助手数据库迁移脚本 (SQLite)
-- 创建日期: 2026-02-15
-- 功能: AI项目计划生成、WBS分解、资源分配

-- ========================================
-- 1. AI项目计划模板表
-- ========================================
CREATE TABLE IF NOT EXISTS ai_project_plan_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- 基础信息
    template_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    industry VARCHAR(50),
    complexity_level VARCHAR(20), -- LOW/MEDIUM/HIGH/CRITICAL
    
    -- AI生成信息
    ai_model_version VARCHAR(50),
    generation_time DATETIME,
    confidence_score DECIMAL(5, 2),
    
    -- 模板内容 (JSON)
    description TEXT,
    phases TEXT, -- JSON: [{name, duration_days, deliverables}]
    milestones TEXT, -- JSON: [{name, phase, estimated_day}]
    risk_factors TEXT, -- JSON: [{category, description, mitigation}]
    
    -- 估算信息
    estimated_duration_days INTEGER,
    estimated_effort_hours DECIMAL(10, 2),
    estimated_cost DECIMAL(14, 2),
    
    -- 资源需求 (JSON)
    required_roles TEXT, -- JSON: [{role, skill_level, count}]
    recommended_team_size INTEGER,
    
    -- 参考数据 (JSON)
    reference_project_ids TEXT, -- JSON: [1, 2, 3]
    reference_count INTEGER DEFAULT 0,
    
    -- 使用统计
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2),
    avg_accuracy DECIMAL(5, 2),
    
    -- 审核状态
    is_verified BOOLEAN DEFAULT 0,
    verified_by INTEGER,
    verified_at DATETIME,
    verification_notes TEXT,
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,
    is_recommended BOOLEAN DEFAULT 0,
    
    -- 元数据 (JSON)
    tags TEXT, -- JSON: ["tag1", "tag2"]
    metadata TEXT, -- JSON: {}
    
    -- 创建人
    created_by INTEGER,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (verified_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_template_project_type ON ai_project_plan_templates(project_type);
CREATE INDEX IF NOT EXISTS idx_template_complexity ON ai_project_plan_templates(complexity_level);
CREATE INDEX IF NOT EXISTS idx_template_active ON ai_project_plan_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_template_confidence ON ai_project_plan_templates(confidence_score);

-- ========================================
-- 2. AI WBS分解建议表
-- ========================================
CREATE TABLE IF NOT EXISTS ai_wbs_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- 关联项目
    project_id INTEGER,
    template_id INTEGER,
    
    -- AI生成信息
    ai_model_version VARCHAR(50),
    generation_time DATETIME,
    confidence_score DECIMAL(5, 2),
    
    -- WBS层级结构
    wbs_level INTEGER,
    parent_wbs_id INTEGER,
    wbs_code VARCHAR(50),
    sequence INTEGER,
    
    -- 任务信息
    task_name VARCHAR(200) NOT NULL,
    task_description TEXT,
    task_type VARCHAR(50),
    category VARCHAR(50),
    
    -- 工作量估算
    estimated_duration_days DECIMAL(6, 1),
    estimated_effort_hours DECIMAL(8, 1),
    estimated_cost DECIMAL(12, 2),
    complexity VARCHAR(20), -- SIMPLE/MEDIUM/COMPLEX/CRITICAL
    
    -- 依赖关系 (JSON)
    dependencies TEXT, -- JSON: [{"task_id": 1, "type": "FS"}]
    dependency_type VARCHAR(20), -- FS/SS/FF/SF
    is_critical_path BOOLEAN DEFAULT 0,
    
    -- 资源需求 (JSON)
    required_skills TEXT, -- JSON: [{"skill": "Python", "level": "Senior"}]
    required_roles TEXT, -- JSON: [{"role": "开发", "count": 2}]
    recommended_assignees TEXT, -- JSON: [1, 2, 3]
    
    -- 交付物 (JSON)
    deliverables TEXT, -- JSON: [{name, type, description}]
    acceptance_criteria TEXT,
    
    -- 风险评估 (JSON)
    risk_level VARCHAR(20), -- LOW/MEDIUM/HIGH/CRITICAL
    risk_factors TEXT, -- JSON: [{factor, probability, impact}]
    mitigation_strategies TEXT, -- JSON: [...]
    
    -- 参考数据 (JSON)
    reference_task_ids TEXT, -- JSON: [1, 2, 3]
    similarity_score DECIMAL(5, 2),
    
    -- 用户反馈
    is_accepted BOOLEAN,
    is_modified BOOLEAN DEFAULT 0,
    actual_task_id INTEGER,
    feedback_score INTEGER, -- 1-5
    feedback_notes TEXT,
    
    -- 实际执行对比
    actual_duration_days DECIMAL(6, 1),
    actual_effort_hours DECIMAL(8, 1),
    actual_cost DECIMAL(12, 2),
    variance_duration DECIMAL(6, 1),
    variance_effort DECIMAL(8, 1),
    variance_cost DECIMAL(12, 2),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'SUGGESTED', -- SUGGESTED/ACCEPTED/REJECTED/MODIFIED/COMPLETED
    is_active BOOLEAN DEFAULT 1,
    
    -- 元数据 (JSON)
    tags TEXT, -- JSON: ["tag1", "tag2"]
    metadata TEXT, -- JSON: {}
    
    -- 创建人
    created_by INTEGER,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (template_id) REFERENCES ai_project_plan_templates(id),
    FOREIGN KEY (parent_wbs_id) REFERENCES ai_wbs_suggestions(id),
    FOREIGN KEY (actual_task_id) REFERENCES task_unified(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_wbs_project_id ON ai_wbs_suggestions(project_id);
CREATE INDEX IF NOT EXISTS idx_wbs_template_id ON ai_wbs_suggestions(template_id);
CREATE INDEX IF NOT EXISTS idx_wbs_level ON ai_wbs_suggestions(wbs_level);
CREATE INDEX IF NOT EXISTS idx_wbs_parent ON ai_wbs_suggestions(parent_wbs_id);
CREATE INDEX IF NOT EXISTS idx_wbs_status ON ai_wbs_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_wbs_critical_path ON ai_wbs_suggestions(is_critical_path);

-- ========================================
-- 3. AI资源分配建议表
-- ========================================
CREATE TABLE IF NOT EXISTS ai_resource_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allocation_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- 关联项目和任务
    project_id INTEGER NOT NULL,
    wbs_suggestion_id INTEGER,
    task_id INTEGER,
    
    -- AI生成信息
    ai_model_version VARCHAR(50),
    generation_time DATETIME,
    confidence_score DECIMAL(5, 2),
    optimization_method VARCHAR(50), -- GENETIC/GREEDY/SIMULATED_ANNEALING
    
    -- 资源信息
    user_id INTEGER NOT NULL,
    role_name VARCHAR(50),
    allocation_type VARCHAR(20), -- PRIMARY/SECONDARY/BACKUP/REVIEWER
    
    -- 时间分配
    planned_start_date DATE,
    planned_end_date DATE,
    allocated_hours DECIMAL(8, 1),
    workload_percentage DECIMAL(5, 2),
    
    -- 匹配度分析
    skill_match_score DECIMAL(5, 2),
    experience_match_score DECIMAL(5, 2),
    availability_score DECIMAL(5, 2),
    performance_score DECIMAL(5, 2),
    overall_match_score DECIMAL(5, 2),
    
    -- 技能要求匹配 (JSON)
    required_skills TEXT, -- JSON: [{skill, level, weight}]
    user_skills TEXT, -- JSON: [{skill, level, experience_years}]
    skill_gaps TEXT, -- JSON: [{skill, required_level, current_level}]
    
    -- 可用性分析
    current_workload DECIMAL(5, 2),
    concurrent_tasks INTEGER,
    is_available BOOLEAN DEFAULT 1,
    availability_notes TEXT,
    conflicts TEXT, -- JSON: [{task_id, task_name, overlap_days}]
    
    -- 历史绩效
    similar_task_count INTEGER,
    avg_task_completion_rate DECIMAL(5, 2),
    avg_quality_score DECIMAL(5, 2),
    avg_on_time_rate DECIMAL(5, 2),
    
    -- 成本信息
    hourly_rate DECIMAL(10, 2),
    estimated_cost DECIMAL(12, 2),
    cost_efficiency_score DECIMAL(5, 2),
    
    -- 推荐理由
    recommendation_reason TEXT,
    strengths TEXT, -- JSON: [{category, description, score}]
    weaknesses TEXT, -- JSON: [{category, description, impact}]
    alternative_users TEXT, -- JSON: [{user_id, match_score, notes}]
    
    -- 优先级
    priority VARCHAR(20), -- CRITICAL/HIGH/MEDIUM/LOW
    is_mandatory BOOLEAN DEFAULT 0,
    sequence INTEGER,
    
    -- 用户反馈
    is_accepted BOOLEAN,
    is_modified BOOLEAN DEFAULT 0,
    actual_user_id INTEGER,
    modification_reason TEXT,
    feedback_score INTEGER, -- 1-5
    feedback_notes TEXT,
    
    -- 实际执行对比
    actual_start_date DATE,
    actual_end_date DATE,
    actual_hours DECIMAL(8, 1),
    actual_cost DECIMAL(12, 2),
    performance_rating INTEGER, -- 1-5
    completion_quality INTEGER, -- 1-5
    
    -- 学习数据
    prediction_accuracy DECIMAL(5, 2),
    variance_hours DECIMAL(8, 1),
    variance_cost DECIMAL(12, 2),
    lessons_learned TEXT,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'SUGGESTED', -- SUGGESTED/ACCEPTED/REJECTED/MODIFIED/IN_PROGRESS/COMPLETED
    is_active BOOLEAN DEFAULT 1,
    
    -- 元数据 (JSON)
    tags TEXT, -- JSON: ["tag1", "tag2"]
    metadata TEXT, -- JSON: {}
    
    -- 创建人
    created_by INTEGER,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (wbs_suggestion_id) REFERENCES ai_wbs_suggestions(id),
    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (actual_user_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_allocation_project_id ON ai_resource_allocations(project_id);
CREATE INDEX IF NOT EXISTS idx_allocation_wbs_id ON ai_resource_allocations(wbs_suggestion_id);
CREATE INDEX IF NOT EXISTS idx_allocation_user_id ON ai_resource_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_allocation_status ON ai_resource_allocations(status);
CREATE INDEX IF NOT EXISTS idx_allocation_match_score ON ai_resource_allocations(overall_match_score);
CREATE INDEX IF NOT EXISTS idx_allocation_start_date ON ai_resource_allocations(planned_start_date);
CREATE INDEX IF NOT EXISTS idx_allocation_end_date ON ai_resource_allocations(planned_end_date);

-- ========================================
-- 完成提示
-- ========================================
-- AI项目规划助手数据库表创建完成
-- 包含表:
--   1. ai_project_plan_templates (AI项目计划模板)
--   2. ai_wbs_suggestions (AI WBS分解建议)
--   3. ai_resource_allocations (AI资源分配建议)
