-- 销售团队管理表 (MySQL)
-- 支持一人多队的灵活团队结构，用于销售目标管理、团队排名和业绩PK

-- 1. 销售团队表
CREATE TABLE IF NOT EXISTS sales_teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_code VARCHAR(20) UNIQUE NOT NULL COMMENT '团队编码',
    team_name VARCHAR(100) NOT NULL COMMENT '团队名称',
    description TEXT COMMENT '团队描述',
    team_type VARCHAR(20) DEFAULT 'REGION' COMMENT '团队类型：REGION/INDUSTRY/SCALE/OTHER',
    department_id INT COMMENT '所属部门ID',
    leader_id INT COMMENT '团队负责人ID',
    parent_team_id INT COMMENT '上级团队ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序序号',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_sales_team_department FOREIGN KEY (department_id) REFERENCES departments(id),
    CONSTRAINT fk_sales_team_leader FOREIGN KEY (leader_id) REFERENCES users(id),
    CONSTRAINT fk_sales_team_parent FOREIGN KEY (parent_team_id) REFERENCES sales_teams(id),
    CONSTRAINT fk_sales_team_creator FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_sales_team_code (team_code),
    INDEX idx_sales_team_type (team_type),
    INDEX idx_sales_team_department (department_id),
    INDEX idx_sales_team_leader (leader_id),
    INDEX idx_sales_team_parent (parent_team_id),
    INDEX idx_sales_team_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售团队表';

-- 2. 销售团队成员表（多对多）
CREATE TABLE IF NOT EXISTS sales_team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT NOT NULL COMMENT '团队ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role VARCHAR(20) DEFAULT 'MEMBER' COMMENT '成员角色：LEADER/DEPUTY/MEMBER',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否为主团队',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    remark VARCHAR(200) COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_team_member_team FOREIGN KEY (team_id) REFERENCES sales_teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_member_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_team_member (team_id, user_id),

    INDEX idx_team_member_team (team_id),
    INDEX idx_team_member_user (user_id),
    INDEX idx_team_member_role (role),
    INDEX idx_team_member_primary (user_id, is_primary),
    INDEX idx_team_member_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售团队成员表';

-- 3. 团队业绩快照表
CREATE TABLE IF NOT EXISTS team_performance_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT NOT NULL COMMENT '团队ID',
    period_type VARCHAR(20) NOT NULL COMMENT '周期类型：DAILY/WEEKLY/MONTHLY/QUARTERLY',
    period_value VARCHAR(20) NOT NULL COMMENT '周期标识',
    snapshot_date DATETIME NOT NULL COMMENT '快照时间',
    lead_count INT DEFAULT 0 COMMENT '线索数量',
    opportunity_count INT DEFAULT 0 COMMENT '商机数量',
    opportunity_amount DECIMAL(14,2) DEFAULT 0 COMMENT '商机金额',
    contract_count INT DEFAULT 0 COMMENT '签约数量',
    contract_amount DECIMAL(14,2) DEFAULT 0 COMMENT '签约金额',
    collection_amount DECIMAL(14,2) DEFAULT 0 COMMENT '回款金额',
    target_amount DECIMAL(14,2) DEFAULT 0 COMMENT '目标金额',
    completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT '完成率(%)',
    rank_in_department INT COMMENT '部门内排名',
    rank_overall INT COMMENT '全公司排名',
    member_count INT DEFAULT 0 COMMENT '成员数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_team_perf_team FOREIGN KEY (team_id) REFERENCES sales_teams(id) ON DELETE CASCADE,
    UNIQUE KEY uq_team_performance_period (team_id, period_type, period_value),

    INDEX idx_team_perf_team (team_id),
    INDEX idx_team_perf_period (period_type, period_value),
    INDEX idx_team_perf_date (snapshot_date),
    INDEX idx_team_perf_rank (period_type, period_value, rank_overall)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='团队业绩快照表';

-- 4. 团队PK记录表
CREATE TABLE IF NOT EXISTS team_pk_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pk_name VARCHAR(100) NOT NULL COMMENT 'PK名称',
    pk_type VARCHAR(20) NOT NULL COMMENT 'PK类型',
    team_ids TEXT NOT NULL COMMENT '参与团队ID列表(JSON)',
    start_date DATETIME NOT NULL COMMENT '开始时间',
    end_date DATETIME NOT NULL COMMENT '结束时间',
    target_value DECIMAL(14,2) COMMENT 'PK目标值',
    status VARCHAR(20) DEFAULT 'ONGOING' COMMENT '状态',
    winner_team_id INT COMMENT '获胜团队ID',
    result_summary TEXT COMMENT '结果汇总(JSON)',
    reward_description TEXT COMMENT '奖励说明',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_team_pk_winner FOREIGN KEY (winner_team_id) REFERENCES sales_teams(id),
    CONSTRAINT fk_team_pk_creator FOREIGN KEY (created_by) REFERENCES users(id),

    INDEX idx_team_pk_status (status),
    INDEX idx_team_pk_date (start_date, end_date),
    INDEX idx_team_pk_winner (winner_team_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='团队PK记录表';

-- 5. 更新 sales_targets 表
-- 添加外键约束（如果表已存在）
ALTER TABLE sales_targets
ADD CONSTRAINT fk_sales_target_team FOREIGN KEY (team_id) REFERENCES sales_teams(id);

-- 添加索引
CREATE INDEX idx_sales_target_team ON sales_targets(team_id);
