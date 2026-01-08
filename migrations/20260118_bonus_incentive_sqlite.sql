-- ============================================
-- 奖金激励体系模块 - SQLite 迁移
-- 创建日期: 2026-01-18
-- ============================================

-- ============================================
-- 1. 奖金规则表
-- ============================================

CREATE TABLE IF NOT EXISTS bonus_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) UNIQUE NOT NULL,           -- 规则编码
    rule_name VARCHAR(200) NOT NULL,                 -- 规则名称
    bonus_type VARCHAR(20) NOT NULL,                 -- 奖金类型
    calculation_formula TEXT,                        -- 计算公式说明
    base_amount DECIMAL(14, 2),                      -- 基础金额
    coefficient DECIMAL(5, 2),                       -- 系数
    trigger_condition TEXT,                         -- 触发条件(JSON)
    apply_to_roles TEXT,                             -- 适用角色列表(JSON)
    apply_to_depts TEXT,                             -- 适用部门列表(JSON)
    apply_to_projects TEXT,                          -- 适用项目类型列表(JSON)
    effective_start_date DATE,                       -- 生效开始日期
    effective_end_date DATE,                         -- 生效结束日期
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    priority INTEGER DEFAULT 0,                      -- 优先级
    require_approval BOOLEAN DEFAULT 1,               -- 是否需要审批
    approval_workflow TEXT,                          -- 审批流程(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bonus_rule_code ON bonus_rules(rule_code);
CREATE INDEX IF NOT EXISTS idx_bonus_rule_type ON bonus_rules(bonus_type);
CREATE INDEX IF NOT EXISTS idx_bonus_rule_active ON bonus_rules(is_active);

-- ============================================
-- 2. 奖金计算记录表
-- ============================================

CREATE TABLE IF NOT EXISTS bonus_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_code VARCHAR(50) UNIQUE NOT NULL,    -- 计算单号
    rule_id INTEGER NOT NULL,                        -- 规则ID
    period_id INTEGER,                                -- 考核周期ID（绩效奖金）
    project_id INTEGER,                              -- 项目ID（项目奖金）
    milestone_id INTEGER,                            -- 里程碑ID（里程碑奖金）
    user_id INTEGER NOT NULL,                        -- 受益人ID
    performance_result_id INTEGER,                   -- 绩效结果ID
    project_contribution_id INTEGER,                 -- 项目贡献ID
    calculation_basis TEXT,                           -- 计算依据详情(JSON)
    calculated_amount DECIMAL(14, 2) NOT NULL,       -- 计算金额
    calculation_detail TEXT,                          -- 计算明细(JSON)
    status VARCHAR(20) DEFAULT 'CALCULATED',         -- 状态
    approved_by INTEGER,                              -- 审批人
    approved_at DATETIME,                             -- 审批时间
    approval_comment TEXT,                            -- 审批意见
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 计算时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES bonus_rules(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (milestone_id) REFERENCES project_milestones(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (performance_result_id) REFERENCES performance_result(id),
    FOREIGN KEY (project_contribution_id) REFERENCES project_contribution(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bonus_calc_code ON bonus_calculations(calculation_code);
CREATE INDEX IF NOT EXISTS idx_bonus_calc_rule ON bonus_calculations(rule_id);
CREATE INDEX IF NOT EXISTS idx_bonus_calc_user ON bonus_calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_bonus_calc_project ON bonus_calculations(project_id);
CREATE INDEX IF NOT EXISTS idx_bonus_calc_period ON bonus_calculations(period_id);
CREATE INDEX IF NOT EXISTS idx_bonus_calc_status ON bonus_calculations(status);

-- ============================================
-- 3. 奖金发放记录表
-- ============================================

CREATE TABLE IF NOT EXISTS bonus_distributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribution_code VARCHAR(50) UNIQUE NOT NULL,   -- 发放单号
    calculation_id INTEGER NOT NULL,                 -- 计算记录ID
    user_id INTEGER NOT NULL,                        -- 受益人ID
    distributed_amount DECIMAL(14, 2) NOT NULL,      -- 发放金额
    distribution_date DATE NOT NULL,                  -- 发放日期
    payment_method VARCHAR(20),                       -- 发放方式
    status VARCHAR(20) DEFAULT 'PENDING',            -- 状态
    voucher_no VARCHAR(50),                           -- 凭证号
    payment_account VARCHAR(100),                     -- 付款账户
    payment_remark TEXT,                              -- 付款备注
    paid_by INTEGER,                                  -- 发放人
    paid_at DATETIME,                                 -- 发放时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calculation_id) REFERENCES bonus_calculations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (paid_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bonus_dist_code ON bonus_distributions(distribution_code);
CREATE INDEX IF NOT EXISTS idx_bonus_dist_calc ON bonus_distributions(calculation_id);
CREATE INDEX IF NOT EXISTS idx_bonus_dist_user ON bonus_distributions(user_id);
CREATE INDEX IF NOT EXISTS idx_bonus_dist_status ON bonus_distributions(status);
CREATE INDEX IF NOT EXISTS idx_bonus_dist_date ON bonus_distributions(distribution_date);

-- ============================================
-- 4. 团队奖金分配表
-- ============================================

CREATE TABLE IF NOT EXISTS team_bonus_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                      -- 项目ID
    period_id INTEGER,                                 -- 周期ID
    total_bonus_amount DECIMAL(14, 2) NOT NULL,       -- 团队总奖金
    allocation_method VARCHAR(20),                     -- 分配方式
    allocation_detail TEXT,                            -- 分配明细(JSON)
    status VARCHAR(20) DEFAULT 'PENDING',             -- 状态
    approved_by INTEGER,                               -- 审批人
    approved_at DATETIME,                              -- 审批时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_team_bonus_project ON team_bonus_allocations(project_id);
CREATE INDEX IF NOT EXISTS idx_team_bonus_period ON team_bonus_allocations(period_id);
CREATE INDEX IF NOT EXISTS idx_team_bonus_status ON team_bonus_allocations(status);






