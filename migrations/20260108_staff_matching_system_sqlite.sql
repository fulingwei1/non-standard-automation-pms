-- AI驱动人员智能匹配系统 - SQLite数据库迁移
-- 创建时间: 2026-01-08

-- =====================================================
-- 1. 标签字典表 (hr_tag_dict)
-- =====================================================
CREATE TABLE IF NOT EXISTS hr_tag_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_code VARCHAR(50) UNIQUE NOT NULL,           -- 标签编码
    tag_name VARCHAR(100) NOT NULL,                 -- 标签名称
    tag_type VARCHAR(20) NOT NULL,                  -- SKILL/DOMAIN/ATTITUDE/CHARACTER/SPECIAL
    parent_id INTEGER,                              -- 父标签ID（支持层级）
    weight DECIMAL(5,2) DEFAULT 1.0,                -- 权重
    is_required BOOLEAN DEFAULT 0,                  -- 是否必需标签
    description TEXT,                               -- 标签描述
    sort_order INTEGER DEFAULT 0,                   -- 排序
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES hr_tag_dict(id)
);

CREATE INDEX IF NOT EXISTS idx_hr_tag_dict_type ON hr_tag_dict(tag_type);
CREATE INDEX IF NOT EXISTS idx_hr_tag_dict_parent ON hr_tag_dict(parent_id);
CREATE INDEX IF NOT EXISTS idx_hr_tag_dict_active ON hr_tag_dict(is_active);

-- =====================================================
-- 2. 员工标签评估表 (hr_employee_tag_evaluation)
-- =====================================================
CREATE TABLE IF NOT EXISTS hr_employee_tag_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                   -- 员工ID
    tag_id INTEGER NOT NULL,                        -- 标签ID
    score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),  -- 评分1-5
    evidence TEXT,                                  -- 评分依据/证据
    evaluator_id INTEGER NOT NULL,                  -- 评估人ID
    evaluate_date DATE NOT NULL,                    -- 评估日期
    is_valid BOOLEAN DEFAULT 1,                     -- 是否有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (tag_id) REFERENCES hr_tag_dict(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_hr_eval_employee ON hr_employee_tag_evaluation(employee_id);
CREATE INDEX IF NOT EXISTS idx_hr_eval_tag ON hr_employee_tag_evaluation(tag_id);
CREATE INDEX IF NOT EXISTS idx_hr_eval_evaluator ON hr_employee_tag_evaluation(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_hr_eval_date ON hr_employee_tag_evaluation(evaluate_date);
CREATE INDEX IF NOT EXISTS idx_hr_eval_valid ON hr_employee_tag_evaluation(is_valid);

-- =====================================================
-- 3. 员工扩展档案表 (hr_employee_profile)
-- =====================================================
CREATE TABLE IF NOT EXISTS hr_employee_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER UNIQUE NOT NULL,            -- 员工ID
    skill_tags TEXT,                                -- 技能标签JSON [{tag_id, score, tag_name}]
    domain_tags TEXT,                               -- 领域标签JSON
    attitude_tags TEXT,                             -- 态度标签JSON
    character_tags TEXT,                            -- 性格标签JSON
    special_tags TEXT,                              -- 特殊能力JSON
    attitude_score DECIMAL(5,2),                    -- 态度得分（聚合）
    quality_score DECIMAL(5,2),                     -- 质量得分（聚合）
    current_workload_pct DECIMAL(5,2) DEFAULT 0,   -- 当前工作负载百分比
    available_hours DECIMAL(10,2) DEFAULT 0,        -- 可用工时
    total_projects INTEGER DEFAULT 0,               -- 参与项目总数
    avg_performance_score DECIMAL(5,2),             -- 平均绩效得分
    profile_updated_at TIMESTAMP,                   -- 档案更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_hr_profile_employee ON hr_employee_profile(employee_id);
CREATE INDEX IF NOT EXISTS idx_hr_profile_workload ON hr_employee_profile(current_workload_pct);
CREATE INDEX IF NOT EXISTS idx_hr_profile_quality ON hr_employee_profile(quality_score);

-- =====================================================
-- 4. 项目绩效历史表 (hr_project_performance)
-- =====================================================
CREATE TABLE IF NOT EXISTS hr_project_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                   -- 员工ID
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_code VARCHAR(50) NOT NULL,                 -- 角色编码
    role_name VARCHAR(100),                         -- 角色名称
    performance_score DECIMAL(5,2),                 -- 绩效得分
    quality_score DECIMAL(5,2),                     -- 质量得分
    collaboration_score DECIMAL(5,2),               -- 协作得分
    on_time_rate DECIMAL(5,2),                      -- 按时完成率
    contribution_level VARCHAR(20),                 -- CORE/MAJOR/NORMAL/MINOR
    hours_spent DECIMAL(10,2),                      -- 投入工时
    evaluation_date DATE,                           -- 评估日期
    evaluator_id INTEGER,                           -- 评估人ID
    comments TEXT,                                  -- 评价意见
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_hr_perf_employee ON hr_project_performance(employee_id);
CREATE INDEX IF NOT EXISTS idx_hr_perf_project ON hr_project_performance(project_id);
CREATE INDEX IF NOT EXISTS idx_hr_perf_role ON hr_project_performance(role_code);
CREATE INDEX IF NOT EXISTS idx_hr_perf_contribution ON hr_project_performance(contribution_level);
CREATE UNIQUE INDEX IF NOT EXISTS idx_hr_perf_emp_proj ON hr_project_performance(employee_id, project_id);

-- =====================================================
-- 5. 项目人员需求表 (mes_project_staffing_need)
-- =====================================================
CREATE TABLE IF NOT EXISTS mes_project_staffing_need (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_code VARCHAR(50) NOT NULL,                 -- 角色编码
    role_name VARCHAR(100),                         -- 角色名称
    headcount INTEGER DEFAULT 1,                    -- 需求人数
    required_skills TEXT NOT NULL,                  -- 必需技能JSON [{tag_id, min_score}]
    preferred_skills TEXT,                          -- 优选技能JSON
    required_domains TEXT,                          -- 必需领域JSON
    required_attitudes TEXT,                        -- 必需态度JSON
    min_level VARCHAR(20),                          -- 最低等级
    priority VARCHAR(10) DEFAULT 'P3',              -- P1-P5
    start_date DATE,                                -- 开始日期
    end_date DATE,                                  -- 结束日期
    allocation_pct DECIMAL(5,2) DEFAULT 100,        -- 分配比例
    status VARCHAR(20) DEFAULT 'OPEN',              -- OPEN/MATCHING/FILLED/CANCELLED
    requester_id INTEGER,                           -- 申请人ID
    filled_count INTEGER DEFAULT 0,                 -- 已填充人数
    remark TEXT,                                    -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (requester_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_staffing_project ON mes_project_staffing_need(project_id);
CREATE INDEX IF NOT EXISTS idx_staffing_role ON mes_project_staffing_need(role_code);
CREATE INDEX IF NOT EXISTS idx_staffing_priority ON mes_project_staffing_need(priority);
CREATE INDEX IF NOT EXISTS idx_staffing_status ON mes_project_staffing_need(status);
CREATE INDEX IF NOT EXISTS idx_staffing_requester ON mes_project_staffing_need(requester_id);

-- =====================================================
-- 6. AI匹配日志表 (hr_ai_matching_log)
-- =====================================================
CREATE TABLE IF NOT EXISTS hr_ai_matching_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id VARCHAR(50) NOT NULL,                -- 匹配请求ID
    project_id INTEGER NOT NULL,                    -- 项目ID
    staffing_need_id INTEGER NOT NULL,              -- 人员需求ID
    candidate_employee_id INTEGER NOT NULL,         -- 候选员工ID
    total_score DECIMAL(5,2) NOT NULL,              -- 综合得分
    dimension_scores TEXT NOT NULL,                 -- 各维度得分JSON
    rank INTEGER NOT NULL,                          -- 排名
    recommendation_type VARCHAR(20),                -- STRONG/RECOMMENDED/ACCEPTABLE/WEAK
    is_accepted BOOLEAN,                            -- 是否被采纳
    accept_time TIMESTAMP,                          -- 采纳时间
    acceptor_id INTEGER,                            -- 采纳人ID
    reject_reason TEXT,                             -- 拒绝原因
    matching_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 匹配时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (staffing_need_id) REFERENCES mes_project_staffing_need(id),
    FOREIGN KEY (candidate_employee_id) REFERENCES employees(id),
    FOREIGN KEY (acceptor_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_matching_request ON hr_ai_matching_log(request_id);
CREATE INDEX IF NOT EXISTS idx_matching_project ON hr_ai_matching_log(project_id);
CREATE INDEX IF NOT EXISTS idx_matching_need ON hr_ai_matching_log(staffing_need_id);
CREATE INDEX IF NOT EXISTS idx_matching_candidate ON hr_ai_matching_log(candidate_employee_id);
CREATE INDEX IF NOT EXISTS idx_matching_accepted ON hr_ai_matching_log(is_accepted);
CREATE INDEX IF NOT EXISTS idx_matching_time ON hr_ai_matching_log(matching_time);

-- =====================================================
-- 初始数据: 标签字典种子数据
-- =====================================================

-- 技能标签 (SKILL)
INSERT OR IGNORE INTO hr_tag_dict (tag_code, tag_name, tag_type, weight, description, sort_order) VALUES
('SKILL_ME_DESIGN', '机械设计', 'SKILL', 1.0, '机械结构设计能力', 1),
('SKILL_ME_3D', '3D建模', 'SKILL', 1.0, 'SolidWorks/UG等3D建模', 2),
('SKILL_ME_2D', '工程制图', 'SKILL', 0.8, 'AutoCAD工程图纸', 3),
('SKILL_EE_SCHEMATIC', '电气原理图', 'SKILL', 1.0, '电气原理图设计', 4),
('SKILL_EE_PLC', 'PLC编程', 'SKILL', 1.2, 'PLC程序编写调试', 5),
('SKILL_EE_HMI', 'HMI开发', 'SKILL', 0.9, '触摸屏界面开发', 6),
('SKILL_SW_MOTION', '运动控制', 'SKILL', 1.2, '运动控制系统开发', 7),
('SKILL_SW_VISION', '视觉系统', 'SKILL', 1.3, '视觉检测系统开发', 8),
('SKILL_TE_ICT', 'ICT测试', 'SKILL', 1.0, 'ICT测试设备调试', 9),
('SKILL_TE_FCT', 'FCT测试', 'SKILL', 1.0, 'FCT功能测试', 10),
('SKILL_ASSEMBLY', '装配调试', 'SKILL', 1.0, '设备装配调试能力', 11),
('SKILL_DEBUG', '故障排除', 'SKILL', 1.1, '设备故障诊断排除', 12);

-- 领域标签 (DOMAIN)
INSERT OR IGNORE INTO hr_tag_dict (tag_code, tag_name, tag_type, weight, description, sort_order) VALUES
('DOMAIN_3C', '3C电子', 'DOMAIN', 1.0, '3C电子行业经验', 1),
('DOMAIN_AUTO', '汽车电子', 'DOMAIN', 1.2, '汽车电子行业经验', 2),
('DOMAIN_MEDICAL', '医疗器械', 'DOMAIN', 1.3, '医疗器械行业经验', 3),
('DOMAIN_SEMICONDUCTOR', '半导体', 'DOMAIN', 1.4, '半导体行业经验', 4),
('DOMAIN_NEW_ENERGY', '新能源', 'DOMAIN', 1.2, '新能源行业经验', 5),
('DOMAIN_PCBA', 'PCBA测试', 'DOMAIN', 1.0, 'PCBA测试经验', 6);

-- 态度标签 (ATTITUDE)
INSERT OR IGNORE INTO hr_tag_dict (tag_code, tag_name, tag_type, weight, description, sort_order) VALUES
('ATT_RESPONSIBLE', '责任心', 'ATTITUDE', 1.2, '工作责任心强', 1),
('ATT_PROACTIVE', '主动性', 'ATTITUDE', 1.1, '工作主动积极', 2),
('ATT_TEAMWORK', '团队协作', 'ATTITUDE', 1.0, '善于团队协作', 3),
('ATT_LEARNING', '学习能力', 'ATTITUDE', 1.0, '快速学习能力', 4),
('ATT_PRESSURE', '抗压能力', 'ATTITUDE', 1.1, '能承受工作压力', 5),
('ATT_COMMUNICATION', '沟通能力', 'ATTITUDE', 1.0, '有效沟通能力', 6);

-- 性格标签 (CHARACTER)
INSERT OR IGNORE INTO hr_tag_dict (tag_code, tag_name, tag_type, weight, description, sort_order) VALUES
('CHAR_DETAIL', '细致严谨', 'CHARACTER', 1.0, '工作细致严谨', 1),
('CHAR_CREATIVE', '创新思维', 'CHARACTER', 0.9, '具有创新思维', 2),
('CHAR_STABLE', '稳重可靠', 'CHARACTER', 1.0, '性格稳重可靠', 3),
('CHAR_FLEXIBLE', '灵活应变', 'CHARACTER', 0.8, '灵活应变能力', 4);

-- 特殊能力标签 (SPECIAL)
INSERT OR IGNORE INTO hr_tag_dict (tag_code, tag_name, tag_type, weight, description, sort_order) VALUES
('SPEC_ONSITE', '现场经验', 'SPECIAL', 1.5, '客户现场服务经验', 1),
('SPEC_TRAINING', '培训能力', 'SPECIAL', 1.2, '能进行技术培训', 2),
('SPEC_CUSTOMER', '客户关系', 'SPECIAL', 1.3, '良好客户关系维护', 3),
('SPEC_LEADER', '项目带队', 'SPECIAL', 1.4, '能带领项目团队', 4),
('SPEC_OVERSEAS', '出国经验', 'SPECIAL', 1.5, '有海外项目经验', 5);
