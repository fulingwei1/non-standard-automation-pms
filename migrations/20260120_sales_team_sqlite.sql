-- 销售团队管理表 (SQLite)
-- 支持一人多队的灵活团队结构，用于销售目标管理、团队排名和业绩PK

-- 1. 销售团队表
CREATE TABLE IF NOT EXISTS sales_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code VARCHAR(20) UNIQUE NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    description TEXT,
    team_type VARCHAR(20) DEFAULT 'REGION',
    department_id INTEGER REFERENCES departments(id),
    leader_id INTEGER REFERENCES users(id),
    parent_team_id INTEGER REFERENCES sales_teams(id),
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_team_code ON sales_teams(team_code);
CREATE INDEX IF NOT EXISTS idx_sales_team_type ON sales_teams(team_type);
CREATE INDEX IF NOT EXISTS idx_sales_team_department ON sales_teams(department_id);
CREATE INDEX IF NOT EXISTS idx_sales_team_leader ON sales_teams(leader_id);
CREATE INDEX IF NOT EXISTS idx_sales_team_parent ON sales_teams(parent_team_id);
CREATE INDEX IF NOT EXISTS idx_sales_team_active ON sales_teams(is_active);

-- 2. 销售团队成员表（多对多）
CREATE TABLE IF NOT EXISTS sales_team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES sales_teams(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'MEMBER',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    remark VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_team_member_team ON sales_team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_member_user ON sales_team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_member_role ON sales_team_members(role);
CREATE INDEX IF NOT EXISTS idx_team_member_primary ON sales_team_members(user_id, is_primary);
CREATE INDEX IF NOT EXISTS idx_team_member_active ON sales_team_members(is_active);

-- 3. 团队业绩快照表
CREATE TABLE IF NOT EXISTS team_performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES sales_teams(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL,
    period_value VARCHAR(20) NOT NULL,
    snapshot_date DATETIME NOT NULL,
    lead_count INTEGER DEFAULT 0,
    opportunity_count INTEGER DEFAULT 0,
    opportunity_amount DECIMAL(14,2) DEFAULT 0,
    contract_count INTEGER DEFAULT 0,
    contract_amount DECIMAL(14,2) DEFAULT 0,
    collection_amount DECIMAL(14,2) DEFAULT 0,
    target_amount DECIMAL(14,2) DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,
    rank_in_department INTEGER,
    rank_overall INTEGER,
    member_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, period_type, period_value)
);

CREATE INDEX IF NOT EXISTS idx_team_perf_team ON team_performance_snapshots(team_id);
CREATE INDEX IF NOT EXISTS idx_team_perf_period ON team_performance_snapshots(period_type, period_value);
CREATE INDEX IF NOT EXISTS idx_team_perf_date ON team_performance_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_team_perf_rank ON team_performance_snapshots(period_type, period_value, rank_overall);

-- 4. 团队PK记录表
CREATE TABLE IF NOT EXISTS team_pk_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pk_name VARCHAR(100) NOT NULL,
    pk_type VARCHAR(20) NOT NULL,
    team_ids TEXT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    target_value DECIMAL(14,2),
    status VARCHAR(20) DEFAULT 'ONGOING',
    winner_team_id INTEGER REFERENCES sales_teams(id),
    result_summary TEXT,
    reward_description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_team_pk_status ON team_pk_records(status);
CREATE INDEX IF NOT EXISTS idx_team_pk_date ON team_pk_records(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_team_pk_winner ON team_pk_records(winner_team_id);

-- 5. 更新 sales_targets 表，添加团队索引
CREATE INDEX IF NOT EXISTS idx_sales_target_team ON sales_targets(team_id);
