-- migrations/20260121_pitfall_sqlite.sql
-- 踩坑库数据库迁移

-- 踩坑记录表
CREATE TABLE IF NOT EXISTS pitfalls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_no VARCHAR(50) UNIQUE NOT NULL,

    -- 必填字段
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    solution TEXT,

    -- 多维度分类
    stage VARCHAR(20),
    equipment_type VARCHAR(50),
    problem_type VARCHAR(50),
    tags JSON,

    -- 选填字段
    root_cause TEXT,
    impact TEXT,
    prevention TEXT,
    cost_impact DECIMAL(12,2),
    schedule_impact INTEGER,

    -- 来源追溯
    source_type VARCHAR(20),
    source_project_id INTEGER REFERENCES projects(id),
    source_ecn_id INTEGER,
    source_issue_id INTEGER,

    -- 权限与状态
    is_sensitive BOOLEAN DEFAULT FALSE,
    sensitive_reason VARCHAR(50),
    visible_to JSON,
    status VARCHAR(20) DEFAULT 'DRAFT',
    verified BOOLEAN DEFAULT FALSE,
    verify_count INTEGER DEFAULT 0,

    -- 创建人
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pitfall_stage ON pitfalls(stage);
CREATE INDEX IF NOT EXISTS idx_pitfall_equipment ON pitfalls(equipment_type);
CREATE INDEX IF NOT EXISTS idx_pitfall_problem ON pitfalls(problem_type);
CREATE INDEX IF NOT EXISTS idx_pitfall_status ON pitfalls(status);
CREATE INDEX IF NOT EXISTS idx_pitfall_project ON pitfalls(source_project_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_created_by ON pitfalls(created_by);

-- 推荐记录表
CREATE TABLE IF NOT EXISTS pitfall_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    trigger_type VARCHAR(20) NOT NULL,
    trigger_context JSON,

    is_helpful BOOLEAN,
    feedback TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pitfall_rec_project ON pitfall_recommendations(project_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_rec_pitfall ON pitfall_recommendations(pitfall_id);

-- 学习进度表
CREATE TABLE IF NOT EXISTS pitfall_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),

    read_at DATETIME,
    is_marked BOOLEAN DEFAULT FALSE,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, pitfall_id)
);

CREATE INDEX IF NOT EXISTS idx_pitfall_learn_user ON pitfall_learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_learn_pitfall ON pitfall_learning_progress(pitfall_id);
