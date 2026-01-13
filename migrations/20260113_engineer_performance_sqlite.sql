-- =====================================================
-- 工程师绩效系统集成 - SQLite 迁移脚本
-- 日期: 2026-01-13
-- 说明: 扩展现有绩效系统，增加工程师专属评价功能
-- =====================================================

-- =====================================================
-- 1. 修改现有表：performance_result 增加字段
-- =====================================================

-- 添加岗位类型字段
ALTER TABLE performance_result ADD COLUMN job_type VARCHAR(20);

-- 添加职级字段
ALTER TABLE performance_result ADD COLUMN job_level VARCHAR(20);

-- 添加五维详细得分 JSON 字段
ALTER TABLE performance_result ADD COLUMN dimension_details TEXT;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_perf_result_job_type ON performance_result(job_type);
CREATE INDEX IF NOT EXISTS idx_perf_result_job_level ON performance_result(job_level);

-- =====================================================
-- 2. 新增核心表：工程师档案
-- =====================================================

CREATE TABLE IF NOT EXISTS engineer_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,

    -- 岗位信息
    job_type VARCHAR(20) NOT NULL,
    job_level VARCHAR(20) DEFAULT 'junior',

    -- 技能标签
    skills TEXT,
    certifications TEXT,

    -- 时间信息
    job_start_date DATE,
    level_start_date DATE,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_engineer_profile_job_type ON engineer_profile(job_type);
CREATE INDEX idx_engineer_profile_job_level ON engineer_profile(job_level);
CREATE INDEX idx_engineer_profile_user ON engineer_profile(user_id);

-- =====================================================
-- 3. 新增核心表：五维权重配置
-- =====================================================

CREATE TABLE IF NOT EXISTS engineer_dimension_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 配置维度（只能按岗位+级别配置，不能针对个人）
    job_type VARCHAR(20) NOT NULL,
    job_level VARCHAR(20),

    -- 五维权重（百分比，总和100）
    technical_weight INTEGER DEFAULT 30,
    execution_weight INTEGER DEFAULT 25,
    cost_quality_weight INTEGER DEFAULT 20,
    knowledge_weight INTEGER DEFAULT 15,
    collaboration_weight INTEGER DEFAULT 10,

    -- 生效时间
    effective_date DATE NOT NULL,
    expired_date DATE,

    -- 配置信息
    config_name VARCHAR(100),
    description TEXT,
    operator_id INTEGER,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_dimension_config_unique ON engineer_dimension_config(job_type, job_level, effective_date);

-- =====================================================
-- 4. 新增核心表：跨部门协作评价
-- =====================================================

CREATE TABLE IF NOT EXISTS collaboration_rating (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,

    -- 评价双方
    rater_id INTEGER NOT NULL,
    ratee_id INTEGER NOT NULL,
    rater_job_type VARCHAR(20),
    ratee_job_type VARCHAR(20),

    -- 四维评分（1-5分）
    communication_score INTEGER,
    response_score INTEGER,
    delivery_score INTEGER,
    interface_score INTEGER,

    -- 总分（自动计算）
    total_score DECIMAL(4,2),

    -- 评价备注
    comment TEXT,

    -- 项目关联（可选）
    project_id INTEGER,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (rater_id) REFERENCES users(id),
    FOREIGN KEY (ratee_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_collab_rating_period ON collaboration_rating(period_id);
CREATE INDEX idx_collab_rating_rater ON collaboration_rating(rater_id);
CREATE INDEX idx_collab_rating_ratee ON collaboration_rating(ratee_id);
CREATE UNIQUE INDEX idx_collab_rating_unique ON collaboration_rating(period_id, rater_id, ratee_id);

-- =====================================================
-- 5. 新增核心表：知识贡献记录
-- =====================================================

CREATE TABLE IF NOT EXISTS knowledge_contribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 贡献类型
    contribution_type VARCHAR(30) NOT NULL,
    job_type VARCHAR(20),

    -- 贡献内容
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    tags TEXT,

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 审核状态
    status VARCHAR(20) DEFAULT 'draft',
    approved_by INTEGER,
    approved_at DATETIME,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX idx_knowledge_contrib_user ON knowledge_contribution(contributor_id);
CREATE INDEX idx_knowledge_contrib_type ON knowledge_contribution(contribution_type);
CREATE INDEX idx_knowledge_contrib_job_type ON knowledge_contribution(job_type);
CREATE INDEX idx_knowledge_contrib_status ON knowledge_contribution(status);

-- =====================================================
-- 6. 新增核心表：知识复用记录
-- =====================================================

CREATE TABLE IF NOT EXISTS knowledge_reuse_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    project_id INTEGER,

    -- 复用信息
    reuse_type VARCHAR(30),
    rating INTEGER,
    feedback TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contribution_id) REFERENCES knowledge_contribution(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_knowledge_reuse_contrib ON knowledge_reuse_log(contribution_id);
CREATE INDEX idx_knowledge_reuse_user ON knowledge_reuse_log(user_id);

-- =====================================================
-- 7. 机械工程师专属表：设计评审记录
-- =====================================================

CREATE TABLE IF NOT EXISTS design_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 设计信息
    design_name VARCHAR(200) NOT NULL,
    design_type VARCHAR(50),
    design_code VARCHAR(50),
    version VARCHAR(20),

    -- 评审信息
    review_date DATE,
    reviewer_id INTEGER,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    review_comments TEXT,

    -- 附件
    attachments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX idx_design_review_project ON design_review(project_id);
CREATE INDEX idx_design_review_designer ON design_review(designer_id);
CREATE INDEX idx_design_review_date ON design_review(review_date);
CREATE INDEX idx_design_review_result ON design_review(result);

-- =====================================================
-- 8. 机械工程师专属表：调试问题记录
-- =====================================================

CREATE TABLE IF NOT EXISTS mechanical_debug_issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    responsible_id INTEGER NOT NULL,
    reporter_id INTEGER,

    -- 问题信息
    issue_code VARCHAR(50),
    issue_description TEXT NOT NULL,
    severity VARCHAR(20),
    root_cause VARCHAR(50),
    affected_part VARCHAR(200),

    -- 处理状态
    status VARCHAR(20) DEFAULT 'open',
    found_date DATE,
    resolved_date DATE,
    resolution TEXT,

    -- 影响评估
    cost_impact DECIMAL(12,2),
    time_impact_hours DECIMAL(6,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (responsible_id) REFERENCES users(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);

CREATE INDEX idx_mech_debug_project ON mechanical_debug_issue(project_id);
CREATE INDEX idx_mech_debug_responsible ON mechanical_debug_issue(responsible_id);
CREATE INDEX idx_mech_debug_severity ON mechanical_debug_issue(severity);
CREATE INDEX idx_mech_debug_status ON mechanical_debug_issue(status);

-- =====================================================
-- 9. 机械工程师专属表：设计复用记录
-- =====================================================

CREATE TABLE IF NOT EXISTS design_reuse_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 复用信息
    source_design_id INTEGER,
    source_design_name VARCHAR(200),
    source_project_id INTEGER,

    -- 复用程度
    reuse_type VARCHAR(30),
    reuse_percentage DECIMAL(5,2),

    -- 节省评估
    saved_hours DECIMAL(6,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (source_project_id) REFERENCES projects(id)
);

CREATE INDEX idx_design_reuse_project ON design_reuse_record(project_id);
CREATE INDEX idx_design_reuse_designer ON design_reuse_record(designer_id);

-- =====================================================
-- 10. 测试工程师专属表：Bug记录
-- =====================================================

CREATE TABLE IF NOT EXISTS test_bug_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    reporter_id INTEGER,
    assignee_id INTEGER NOT NULL,

    -- Bug信息
    bug_code VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    bug_type VARCHAR(30),
    found_stage VARCHAR(30),

    -- 处理信息
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'normal',
    found_time DATETIME,
    resolved_time DATETIME,
    fix_duration_hours DECIMAL(6,2),
    resolution TEXT,

    -- 附件
    attachments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);

CREATE INDEX idx_test_bug_project ON test_bug_record(project_id);
CREATE INDEX idx_test_bug_assignee ON test_bug_record(assignee_id);
CREATE INDEX idx_test_bug_severity ON test_bug_record(severity);
CREATE INDEX idx_test_bug_status ON test_bug_record(status);
CREATE INDEX idx_test_bug_stage ON test_bug_record(found_stage);

-- =====================================================
-- 11. 测试工程师专属表：代码评审记录
-- =====================================================

CREATE TABLE IF NOT EXISTS code_review_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    author_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,

    -- 评审信息
    review_title VARCHAR(200),
    code_module VARCHAR(100),
    language VARCHAR(30),
    lines_changed INTEGER,

    -- 评审结果
    review_date DATE,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    comments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX idx_code_review_project ON code_review_record(project_id);
CREATE INDEX idx_code_review_author ON code_review_record(author_id);
CREATE INDEX idx_code_review_reviewer ON code_review_record(reviewer_id);

-- =====================================================
-- 12. 测试工程师专属表：代码模块库
-- =====================================================

CREATE TABLE IF NOT EXISTS code_module (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_code VARCHAR(50),
    category VARCHAR(50),
    language VARCHAR(30),
    description TEXT,

    -- 版本信息
    version VARCHAR(20),
    repository_url VARCHAR(500),

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    projects_used TEXT,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id)
);

CREATE INDEX idx_code_module_contributor ON code_module(contributor_id);
CREATE INDEX idx_code_module_category ON code_module(category);
CREATE INDEX idx_code_module_language ON code_module(language);

-- =====================================================
-- 13. 电气工程师专属表：电气图纸版本
-- =====================================================

CREATE TABLE IF NOT EXISTS electrical_drawing_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 图纸信息
    drawing_name VARCHAR(200) NOT NULL,
    drawing_code VARCHAR(50),
    drawing_type VARCHAR(50),
    version VARCHAR(20),

    -- 评审结果
    review_date DATE,
    reviewer_id INTEGER,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    review_comments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX idx_elec_drawing_project ON electrical_drawing_version(project_id);
CREATE INDEX idx_elec_drawing_designer ON electrical_drawing_version(designer_id);
CREATE INDEX idx_elec_drawing_type ON electrical_drawing_version(drawing_type);

-- =====================================================
-- 14. 电气工程师专属表：PLC程序版本
-- =====================================================

CREATE TABLE IF NOT EXISTS plc_program_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    programmer_id INTEGER NOT NULL,

    -- 程序信息
    program_name VARCHAR(200) NOT NULL,
    program_code VARCHAR(50),
    plc_brand VARCHAR(30),
    plc_model VARCHAR(50),
    version VARCHAR(20),

    -- 调试结果
    first_debug_date DATE,
    is_first_pass BOOLEAN,
    debug_issues INTEGER DEFAULT 0,
    debug_hours DECIMAL(6,2),

    -- 备注
    remarks TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (programmer_id) REFERENCES users(id)
);

CREATE INDEX idx_plc_program_project ON plc_program_version(project_id);
CREATE INDEX idx_plc_program_programmer ON plc_program_version(programmer_id);
CREATE INDEX idx_plc_program_brand ON plc_program_version(plc_brand);

-- =====================================================
-- 15. 电气工程师专属表：PLC功能块库
-- =====================================================

CREATE TABLE IF NOT EXISTS plc_module_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_code VARCHAR(50),
    category VARCHAR(50),
    plc_brand VARCHAR(30),
    description TEXT,

    -- 版本信息
    version VARCHAR(20),
    file_path VARCHAR(500),

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    projects_used TEXT,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id)
);

CREATE INDEX idx_plc_module_contributor ON plc_module_library(contributor_id);
CREATE INDEX idx_plc_module_category ON plc_module_library(category);
CREATE INDEX idx_plc_module_brand ON plc_module_library(plc_brand);

-- =====================================================
-- 16. 电气工程师专属表：元器件选型记录
-- =====================================================

CREATE TABLE IF NOT EXISTS component_selection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    engineer_id INTEGER NOT NULL,

    -- 选型信息
    component_name VARCHAR(200) NOT NULL,
    component_type VARCHAR(50),
    specification VARCHAR(200),
    manufacturer VARCHAR(100),

    -- 选型结果
    is_standard BOOLEAN DEFAULT FALSE,
    is_from_stock BOOLEAN DEFAULT FALSE,
    selection_result VARCHAR(20),
    replacement_reason TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (engineer_id) REFERENCES users(id)
);

CREATE INDEX idx_comp_selection_project ON component_selection(project_id);
CREATE INDEX idx_comp_selection_engineer ON component_selection(engineer_id);
CREATE INDEX idx_comp_selection_type ON component_selection(component_type);

-- =====================================================
-- 17. 电气工程师专属表：电气故障记录
-- =====================================================

CREATE TABLE IF NOT EXISTS electrical_fault_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    responsible_id INTEGER NOT NULL,
    reporter_id INTEGER,

    -- 故障信息
    fault_code VARCHAR(50),
    fault_description TEXT NOT NULL,
    fault_type VARCHAR(50),
    severity VARCHAR(20),

    -- 处理状态
    status VARCHAR(20) DEFAULT 'open',
    found_date DATE,
    resolved_date DATE,
    resolution TEXT,
    root_cause TEXT,

    -- 影响评估
    downtime_hours DECIMAL(6,2),
    cost_impact DECIMAL(12,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (responsible_id) REFERENCES users(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);

CREATE INDEX idx_elec_fault_project ON electrical_fault_record(project_id);
CREATE INDEX idx_elec_fault_responsible ON electrical_fault_record(responsible_id);
CREATE INDEX idx_elec_fault_severity ON electrical_fault_record(severity);
CREATE INDEX idx_elec_fault_status ON electrical_fault_record(status);

-- =====================================================
-- 18. 插入默认五维权重配置
-- =====================================================

INSERT INTO engineer_dimension_config (
    job_type, job_level,
    technical_weight, execution_weight, cost_quality_weight, knowledge_weight, collaboration_weight,
    effective_date, config_name
) VALUES
    ('mechanical', NULL, 30, 25, 20, 15, 10, '2026-01-01', '机械工程师默认配置'),
    ('test', NULL, 30, 25, 20, 15, 10, '2026-01-01', '测试工程师默认配置'),
    ('electrical', NULL, 30, 25, 20, 15, 10, '2026-01-01', '电气工程师默认配置');
