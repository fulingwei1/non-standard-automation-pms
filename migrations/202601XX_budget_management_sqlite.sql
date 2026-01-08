-- 项目预算管理模块 - SQLite 迁移文件
-- 创建日期：2025-01-XX

-- ============================================
-- 1. 项目预算表
-- ============================================

CREATE TABLE IF NOT EXISTS project_budgets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_no           VARCHAR(50) UNIQUE NOT NULL,                   -- 预算编号
    project_id          INTEGER NOT NULL,                              -- 项目ID
    budget_name         VARCHAR(200) NOT NULL,                         -- 预算名称
    budget_type         VARCHAR(20) DEFAULT 'INITIAL',                 -- 预算类型：INITIAL/REVISED/SUPPLEMENT
    version             VARCHAR(20) DEFAULT 'V1.0',                   -- 预算版本号
    total_amount        NUMERIC(14, 2) NOT NULL DEFAULT 0,            -- 预算总额
    budget_breakdown    TEXT,                                          -- 预算明细（JSON格式）
    status              VARCHAR(20) DEFAULT 'DRAFT',                   -- 状态：DRAFT/SUBMITTED/APPROVED/REJECTED
    submitted_at        DATETIME,                                      -- 提交时间
    submitted_by        INTEGER,                                       -- 提交人ID
    approved_by         INTEGER,                                       -- 审批人ID
    approved_at         DATETIME,                                       -- 审批时间
    approval_note        TEXT,                                          -- 审批意见
    effective_date      DATE,                                           -- 生效日期
    expiry_date         DATE,                                          -- 失效日期
    is_active           BOOLEAN DEFAULT 1,                            -- 是否生效
    remark              TEXT,                                           -- 备注
    created_by          INTEGER,                                       -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_budget_project ON project_budgets(project_id);
CREATE INDEX idx_budget_status ON project_budgets(status);
CREATE INDEX idx_budget_version ON project_budgets(project_id, version);

-- ============================================
-- 2. 项目预算明细表
-- ============================================

CREATE TABLE IF NOT EXISTS project_budget_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id           INTEGER NOT NULL,                              -- 预算ID
    item_no             INTEGER NOT NULL,                              -- 行号
    cost_category       VARCHAR(50) NOT NULL,                           -- 成本类别
    cost_item           VARCHAR(200) NOT NULL,                          -- 成本项
    description         TEXT,                                           -- 说明
    budget_amount       NUMERIC(14, 2) NOT NULL DEFAULT 0,            -- 预算金额
    machine_id          INTEGER,                                       -- 机台ID（可选）
    remark              TEXT,                                           -- 备注
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (budget_id) REFERENCES project_budgets(id) ON DELETE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE INDEX idx_budget_item_budget ON project_budget_items(budget_id);
CREATE INDEX idx_budget_item_category ON project_budget_items(cost_category);

-- ============================================
-- 3. 项目成本分摊规则表
-- ============================================

CREATE TABLE IF NOT EXISTS project_cost_allocation_rules (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name           VARCHAR(100) NOT NULL,                          -- 规则名称
    rule_type           VARCHAR(20) NOT NULL,                           -- 分摊类型：PROPORTION/MANUAL
    allocation_basis    VARCHAR(20) NOT NULL,                           -- 分摊依据：MACHINE_COUNT/REVENUE/MANUAL
    allocation_formula  TEXT,                                           -- 分摊公式（JSON格式）
    cost_type           VARCHAR(50),                                     -- 适用成本类型
    cost_category       VARCHAR(50),                                     -- 适用成本分类
    project_ids         TEXT,                                           -- 适用项目ID列表（JSON）
    is_active           BOOLEAN DEFAULT 1,                             -- 是否启用
    effective_date       DATE,                                           -- 生效日期
    expiry_date         DATE,                                           -- 失效日期
    remark              TEXT,                                           -- 备注
    created_by          INTEGER,                                        -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_allocation_rule_name ON project_cost_allocation_rules(rule_name);
CREATE INDEX idx_allocation_rule_type ON project_cost_allocation_rules(rule_type);






