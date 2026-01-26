-- BEM 战略管理模块迁移脚本 (SQLite)
-- 创建时间: 2026-01-20
-- 模块: 战略管理 (Strategy Management)

-- ============================================
-- 1. 战略主表
-- ============================================
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,          -- 战略编码，如 STR-2026
    name VARCHAR(200) NOT NULL,                -- 战略名称
    vision TEXT,                               -- 愿景描述
    mission TEXT,                              -- 使命描述
    slogan VARCHAR(200),                       -- 战略口号

    year INTEGER NOT NULL,                     -- 战略年度
    start_date DATE,                           -- 战略周期开始
    end_date DATE,                             -- 战略周期结束

    status VARCHAR(20) DEFAULT 'DRAFT',        -- 状态：DRAFT/ACTIVE/ARCHIVED

    created_by INTEGER REFERENCES users(id),   -- 创建人
    approved_by INTEGER REFERENCES users(id),  -- 审批人
    approved_at DATETIME,                      -- 审批时间
    published_at DATETIME,                     -- 发布时间

    is_active BOOLEAN DEFAULT 1,               -- 是否激活
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategies_code ON strategies(code);
CREATE INDEX IF NOT EXISTS idx_strategies_year ON strategies(year);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(is_active);

-- ============================================
-- 2. 关键成功要素 (CSF)
-- ============================================
CREATE TABLE IF NOT EXISTS csfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    dimension VARCHAR(20) NOT NULL,            -- BSC维度：FINANCIAL/CUSTOMER/INTERNAL/LEARNING
    code VARCHAR(50) NOT NULL,                 -- CSF 编码，如 CSF-F-001
    name VARCHAR(200) NOT NULL,                -- 要素名称
    description TEXT,                          -- 详细描述

    derivation_method VARCHAR(50),             -- 导出方法
    weight DECIMAL(5,2) DEFAULT 0,             -- 权重占比
    sort_order INTEGER DEFAULT 0,              -- 排序

    owner_dept_id INTEGER REFERENCES departments(id),
    owner_user_id INTEGER REFERENCES users(id),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_csfs_strategy ON csfs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_csfs_dimension ON csfs(dimension);
CREATE INDEX IF NOT EXISTS idx_csfs_code ON csfs(code);
CREATE INDEX IF NOT EXISTS idx_csfs_owner_dept ON csfs(owner_dept_id);
CREATE INDEX IF NOT EXISTS idx_csfs_active ON csfs(is_active);

-- ============================================
-- 3. KPI 指标
-- ============================================
CREATE TABLE IF NOT EXISTS kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csf_id INTEGER NOT NULL REFERENCES csfs(id),

    code VARCHAR(50) NOT NULL,                 -- KPI 编码
    name VARCHAR(200) NOT NULL,                -- 指标名称
    description TEXT,                          -- 指标描述

    ipooc_type VARCHAR(20) NOT NULL,           -- IPOOC类型
    unit VARCHAR(20),                          -- 单位
    direction VARCHAR(10) DEFAULT 'UP',        -- 方向：UP/DOWN

    target_value DECIMAL(14,2),                -- 目标值
    baseline_value DECIMAL(14,2),              -- 基线值
    current_value DECIMAL(14,2),               -- 当前值

    excellent_threshold DECIMAL(14,2),         -- 优秀阈值
    good_threshold DECIMAL(14,2),              -- 良好阈值
    warning_threshold DECIMAL(14,2),           -- 警告阈值

    data_source_type VARCHAR(20) DEFAULT 'MANUAL',
    data_source_config TEXT,                   -- JSON

    frequency VARCHAR(20) DEFAULT 'MONTHLY',
    last_collected_at DATETIME,

    weight DECIMAL(5,2) DEFAULT 0,
    owner_user_id INTEGER REFERENCES users(id),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpis_csf ON kpis(csf_id);
CREATE INDEX IF NOT EXISTS idx_kpis_code ON kpis(code);
CREATE INDEX IF NOT EXISTS idx_kpis_ipooc ON kpis(ipooc_type);
CREATE INDEX IF NOT EXISTS idx_kpis_source_type ON kpis(data_source_type);
CREATE INDEX IF NOT EXISTS idx_kpis_owner ON kpis(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_kpis_active ON kpis(is_active);

-- ============================================
-- 4. KPI 历史快照
-- ============================================
CREATE TABLE IF NOT EXISTS kpi_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER NOT NULL REFERENCES kpis(id),

    snapshot_date DATE NOT NULL,               -- 快照日期
    snapshot_period VARCHAR(20),               -- 快照周期

    value DECIMAL(14,2),                       -- KPI 值
    target_value DECIMAL(14,2),                -- 目标值
    completion_rate DECIMAL(5,2),              -- 完成率
    health_level VARCHAR(20),                  -- 健康等级

    source_type VARCHAR(20),                   -- 来源类型
    source_detail TEXT,                        -- 来源详情
    remark TEXT,                               -- 备注

    recorded_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpi_history_kpi ON kpi_history(kpi_id);
CREATE INDEX IF NOT EXISTS idx_kpi_history_date ON kpi_history(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_kpi_history_kpi_date ON kpi_history(kpi_id, snapshot_date);

-- ============================================
-- 5. KPI 数据源配置
-- ============================================
CREATE TABLE IF NOT EXISTS kpi_data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER NOT NULL REFERENCES kpis(id),

    source_type VARCHAR(20) NOT NULL,          -- 类型：AUTO/FORMULA

    source_module VARCHAR(50),                 -- 来源模块
    query_type VARCHAR(20),                    -- 查询类型
    metric VARCHAR(100),                       -- 度量字段
    filters TEXT,                              -- 过滤条件（JSON）
    aggregation VARCHAR(20),                   -- 聚合方式

    formula TEXT,                              -- 计算公式
    formula_params TEXT,                       -- 公式参数（JSON）

    is_primary BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,

    last_executed_at DATETIME,
    last_result DECIMAL(14,2),
    last_error TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpi_data_source_kpi ON kpi_data_sources(kpi_id);
CREATE INDEX IF NOT EXISTS idx_kpi_data_source_type ON kpi_data_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_kpi_data_source_active ON kpi_data_sources(is_active);

-- ============================================
-- 6. 年度重点工作
-- ============================================
CREATE TABLE IF NOT EXISTS annual_key_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csf_id INTEGER NOT NULL REFERENCES csfs(id),

    code VARCHAR(50) NOT NULL,                 -- 工作编码
    name VARCHAR(200) NOT NULL,                -- 工作名称
    description TEXT,                          -- 工作描述

    voc_source VARCHAR(20),                    -- 声音来源
    pain_point TEXT,                           -- 痛点/短板
    solution TEXT,                             -- 解决方案
    target TEXT,                               -- 目标描述

    year INTEGER NOT NULL,                     -- 年度
    start_date DATE,                           -- 计划开始
    end_date DATE,                             -- 计划结束
    actual_start_date DATE,                    -- 实际开始
    actual_end_date DATE,                      -- 实际结束

    owner_dept_id INTEGER REFERENCES departments(id),
    owner_user_id INTEGER REFERENCES users(id),

    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    progress_percent INTEGER DEFAULT 0,
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    budget DECIMAL(14,2),
    actual_cost DECIMAL(14,2),

    risk_description TEXT,
    remark TEXT,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_annual_key_works_csf ON annual_key_works(csf_id);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_year ON annual_key_works(year);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_code ON annual_key_works(code);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_status ON annual_key_works(status);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_owner_dept ON annual_key_works(owner_dept_id);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_owner ON annual_key_works(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_active ON annual_key_works(is_active);

-- ============================================
-- 7. 重点工作项目关联
-- ============================================
CREATE TABLE IF NOT EXISTS annual_key_work_project_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annual_work_id INTEGER NOT NULL REFERENCES annual_key_works(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    link_type VARCHAR(20) DEFAULT 'SUPPORT',   -- MAIN/SUPPORT/RELATED
    contribution_weight DECIMAL(5,2) DEFAULT 100,
    remark TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(annual_work_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_akw_project_links_work ON annual_key_work_project_links(annual_work_id);
CREATE INDEX IF NOT EXISTS idx_akw_project_links_project ON annual_key_work_project_links(project_id);

-- ============================================
-- 8. 部门目标
-- ============================================
CREATE TABLE IF NOT EXISTS department_objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),

    year INTEGER NOT NULL,
    quarter INTEGER,

    objectives TEXT,                           -- 部门级目标（JSON）
    key_results TEXT,                          -- 关键成果（JSON）
    kpis_config TEXT,                          -- 部门级 KPI（JSON）

    status VARCHAR(20) DEFAULT 'DRAFT',

    owner_user_id INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at VARCHAR(50),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(strategy_id, department_id, year, quarter)
);

CREATE INDEX IF NOT EXISTS idx_dept_objectives_strategy ON department_objectives(strategy_id);
CREATE INDEX IF NOT EXISTS idx_dept_objectives_dept ON department_objectives(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_objectives_year ON department_objectives(year);
CREATE INDEX IF NOT EXISTS idx_dept_objectives_status ON department_objectives(status);

-- ============================================
-- 9. 个人 KPI
-- ============================================
CREATE TABLE IF NOT EXISTS personal_kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES users(id),

    year INTEGER NOT NULL,
    quarter INTEGER,

    source_type VARCHAR(20) NOT NULL,          -- CSF_KPI/DEPT_OBJECTIVE/ANNUAL_WORK
    source_id INTEGER,
    department_objective_id INTEGER REFERENCES department_objectives(id),

    kpi_name VARCHAR(200) NOT NULL,
    kpi_description TEXT,
    unit VARCHAR(20),

    target_value DECIMAL(14,2),
    actual_value DECIMAL(14,2),
    completion_rate DECIMAL(5,2),

    weight DECIMAL(5,2) DEFAULT 0,

    self_rating INTEGER,
    self_comment TEXT,
    manager_rating INTEGER,
    manager_comment TEXT,

    status VARCHAR(20) DEFAULT 'PENDING',

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_personal_kpis_employee ON personal_kpis(employee_id);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_year ON personal_kpis(year);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_quarter ON personal_kpis(quarter);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_source ON personal_kpis(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_dept_obj ON personal_kpis(department_objective_id);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_status ON personal_kpis(status);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_active ON personal_kpis(is_active);

-- ============================================
-- 10. 战略审视记录
-- ============================================
CREATE TABLE IF NOT EXISTS strategy_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    review_type VARCHAR(20) NOT NULL,          -- ANNUAL/QUARTERLY/MONTHLY/SPECIAL
    review_date DATE NOT NULL,
    review_period VARCHAR(20),

    reviewer_id INTEGER REFERENCES users(id),

    health_score INTEGER,                      -- 总体健康度（0-100）
    financial_score INTEGER,
    customer_score INTEGER,
    internal_score INTEGER,
    learning_score INTEGER,

    findings TEXT,                             -- JSON
    achievements TEXT,                         -- JSON
    recommendations TEXT,                      -- JSON
    decisions TEXT,                            -- JSON
    action_items TEXT,                         -- JSON

    meeting_minutes TEXT,
    attendees TEXT,                            -- JSON
    meeting_duration INTEGER,

    next_review_date DATE,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategy_reviews_strategy ON strategy_reviews(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_reviews_type ON strategy_reviews(review_type);
CREATE INDEX IF NOT EXISTS idx_strategy_reviews_date ON strategy_reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_strategy_reviews_active ON strategy_reviews(is_active);

-- ============================================
-- 11. 战略日历事件
-- ============================================
CREATE TABLE IF NOT EXISTS strategy_calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    event_type VARCHAR(30) NOT NULL,           -- 事件类型
    name VARCHAR(200) NOT NULL,
    description TEXT,

    year INTEGER NOT NULL,
    month INTEGER,
    quarter INTEGER,
    scheduled_date DATE,
    actual_date DATE,
    deadline DATE,

    is_recurring BOOLEAN DEFAULT 0,
    recurrence_rule VARCHAR(50),

    owner_user_id INTEGER REFERENCES users(id),
    participants TEXT,                         -- JSON

    status VARCHAR(20) DEFAULT 'PLANNED',

    review_id INTEGER REFERENCES strategy_reviews(id),

    reminder_days INTEGER DEFAULT 7,
    reminder_sent BOOLEAN DEFAULT 0,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_strategy ON strategy_calendar_events(strategy_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON strategy_calendar_events(event_type);
CREATE INDEX IF NOT EXISTS idx_calendar_events_year ON strategy_calendar_events(year);
CREATE INDEX IF NOT EXISTS idx_calendar_events_month ON strategy_calendar_events(month);
CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON strategy_calendar_events(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON strategy_calendar_events(status);
CREATE INDEX IF NOT EXISTS idx_calendar_events_active ON strategy_calendar_events(is_active);

-- ============================================
-- 12. 战略年度对比
-- ============================================
CREATE TABLE IF NOT EXISTS strategy_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    current_strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    previous_strategy_id INTEGER REFERENCES strategies(id),
    current_year INTEGER NOT NULL,
    previous_year INTEGER,

    generated_date DATE NOT NULL,
    generated_by INTEGER REFERENCES users(id),

    current_health_score INTEGER,
    previous_health_score INTEGER,
    health_change INTEGER,

    current_financial_score INTEGER,
    previous_financial_score INTEGER,
    financial_change INTEGER,

    current_customer_score INTEGER,
    previous_customer_score INTEGER,
    customer_change INTEGER,

    current_internal_score INTEGER,
    previous_internal_score INTEGER,
    internal_change INTEGER,

    current_learning_score INTEGER,
    previous_learning_score INTEGER,
    learning_change INTEGER,

    kpi_completion_rate DECIMAL(5,2),
    previous_kpi_completion_rate DECIMAL(5,2),
    kpi_completion_change DECIMAL(5,2),

    work_completion_rate DECIMAL(5,2),
    previous_work_completion_rate DECIMAL(5,2),
    work_completion_change DECIMAL(5,2),

    csf_comparison TEXT,                       -- JSON
    kpi_comparison TEXT,                       -- JSON
    work_comparison TEXT,                      -- JSON

    summary TEXT,
    highlights TEXT,                           -- JSON
    improvements TEXT,                         -- JSON
    recommendations TEXT,                      -- JSON

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategy_comparison_current ON strategy_comparisons(current_strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_comparison_previous ON strategy_comparisons(previous_strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_comparison_years ON strategy_comparisons(current_year, previous_year);
CREATE INDEX IF NOT EXISTS idx_strategy_comparison_date ON strategy_comparisons(generated_date);
CREATE INDEX IF NOT EXISTS idx_strategy_comparison_active ON strategy_comparisons(is_active);
