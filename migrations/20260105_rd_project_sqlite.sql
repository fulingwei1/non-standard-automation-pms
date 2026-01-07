-- ============================================
-- 研发项目管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 研发项目、项目分类、研发费用、费用类型、费用分摊规则、报表记录
-- 适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
-- ============================================

-- ============================================
-- 1. 研发项目分类表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_project_category (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code       VARCHAR(20) NOT NULL UNIQUE,              -- 分类编码
    category_name       VARCHAR(50) NOT NULL,                    -- 分类名称
    category_type       VARCHAR(20) NOT NULL,                    -- 分类类型：SELF/ENTRUST/COOPERATION
    description         TEXT,                                     -- 分类说明
    sort_order          INTEGER DEFAULT 0,                       -- 排序
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rd_category_code ON rd_project_category(category_code);
CREATE INDEX idx_rd_category_type ON rd_project_category(category_type);

-- ============================================
-- 2. 研发项目主表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_project (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_no          VARCHAR(50) NOT NULL UNIQUE,              -- 研发项目编号
    project_name        VARCHAR(200) NOT NULL,                   -- 研发项目名称
    
    -- 分类信息
    category_id         INTEGER,                                  -- 项目分类ID
    category_type       VARCHAR(20) NOT NULL,                    -- 项目类型：SELF/ENTRUST/COOPERATION
    
    -- 立项信息
    initiation_date     DATE NOT NULL,                           -- 立项日期
    planned_start_date  DATE,                                    -- 计划开始日期
    planned_end_date    DATE,                                    -- 计划结束日期
    actual_start_date   DATE,                                    -- 实际开始日期
    actual_end_date     DATE,                                    -- 实际结束日期
    
    -- 项目负责人
    project_manager_id  INTEGER,                                 -- 项目负责人ID
    project_manager_name VARCHAR(50),                           -- 项目负责人姓名
    
    -- 立项信息
    initiation_reason   TEXT,                                    -- 立项原因
    research_goal       TEXT,                                    -- 研发目标
    research_content    TEXT,                                    -- 研发内容
    expected_result     TEXT,                                    -- 预期成果
    budget_amount       DECIMAL(12,2) DEFAULT 0,                -- 预算金额
    
    -- 关联非标项目
    linked_project_id   INTEGER,                                 -- 关联的非标项目ID
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',            -- 状态：DRAFT/PENDING/APPROVED/IN_PROGRESS/COMPLETED/CANCELLED
    approval_status     VARCHAR(20) DEFAULT 'PENDING',          -- 审批状态：PENDING/APPROVED/REJECTED
    approved_by         INTEGER,                                 -- 审批人ID
    approved_at         DATETIME,                                -- 审批时间
    approval_remark     TEXT,                                    -- 审批意见
    
    -- 结项信息
    close_date          DATE,                                    -- 结项日期
    close_reason        TEXT,                                    -- 结项原因
    close_result        TEXT,                                    -- 结项成果
    closed_by           INTEGER,                                 -- 结项人ID
    
    -- 统计信息
    total_cost          DECIMAL(12,2) DEFAULT 0,                 -- 总费用
    total_hours         DECIMAL(10,2) DEFAULT 0,                -- 总工时
    participant_count   INTEGER DEFAULT 0,                      -- 参与人数
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES rd_project_category(id),
    FOREIGN KEY (project_manager_id) REFERENCES users(id),
    FOREIGN KEY (linked_project_id) REFERENCES projects(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id)
);

CREATE INDEX idx_rd_project_no ON rd_project(project_no);
CREATE INDEX idx_rd_project_category ON rd_project(category_id);
CREATE INDEX idx_rd_project_status ON rd_project(status);
CREATE INDEX idx_rd_project_manager ON rd_project(project_manager_id);
CREATE INDEX idx_rd_project_linked ON rd_project(linked_project_id);

-- ============================================
-- 3. 研发费用类型表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost_type (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code           VARCHAR(20) NOT NULL UNIQUE,              -- 费用类型编码
    type_name           VARCHAR(50) NOT NULL,                    -- 费用类型名称
    category            VARCHAR(20) NOT NULL,                    -- 费用大类：LABOR/MATERIAL/DEPRECIATION/OTHER
    description         TEXT,                                     -- 类型说明
    sort_order          INTEGER DEFAULT 0,                       -- 排序
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    
    -- 加计扣除相关
    is_deductible       BOOLEAN DEFAULT 1,                       -- 是否可加计扣除
    deduction_rate      DECIMAL(5,2) DEFAULT 100.00,             -- 加计扣除比例(%)
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rd_cost_type_code ON rd_cost_type(type_code);
CREATE INDEX idx_rd_cost_type_category ON rd_cost_type(category);

-- ============================================
-- 4. 研发费用分摊规则表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost_allocation_rule (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name           VARCHAR(100) NOT NULL,                   -- 规则名称
    rule_type           VARCHAR(20) NOT NULL,                    -- 分摊类型：PROPORTION/MANUAL
    
    -- 分摊依据
    allocation_basis    VARCHAR(20) NOT NULL,                   -- 分摊依据：HOURS/REVENUE/HEADCOUNT
    allocation_formula  TEXT,                                     -- 分摊公式（JSON格式）
    
    -- 适用范围
    cost_type_ids       TEXT,                                     -- 适用费用类型ID列表（JSON）
    project_ids         TEXT,                                     -- 适用项目ID列表（JSON，空表示全部）
    
    -- 状态
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    effective_date      DATE,                                    -- 生效日期
    expiry_date         DATE,                                    -- 失效日期
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rd_allocation_rule_name ON rd_cost_allocation_rule(rule_name);
CREATE INDEX idx_rd_allocation_rule_type ON rd_cost_allocation_rule(rule_type);

-- ============================================
-- 5. 研发费用表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cost_no             VARCHAR(50) NOT NULL UNIQUE,              -- 费用编号
    
    -- 关联信息
    rd_project_id       INTEGER NOT NULL,                        -- 研发项目ID
    cost_type_id        INTEGER NOT NULL,                        -- 费用类型ID
    
    -- 费用信息
    cost_date           DATE NOT NULL,                           -- 费用发生日期
    cost_amount         DECIMAL(12,2) NOT NULL,                  -- 费用金额
    cost_description    TEXT,                                    -- 费用说明
    
    -- 人工费用相关（如果费用类型是人工）
    user_id             INTEGER,                                 -- 人员ID（人工费用）
    hours               DECIMAL(10,2),                           -- 工时（人工费用）
    hourly_rate         DECIMAL(10,2),                           -- 时薪（人工费用）
    
    -- 材料费用相关（如果费用类型是材料）
    material_id         INTEGER,                                 -- 物料ID（材料费用）
    material_qty        DECIMAL(10,4),                           -- 物料数量（材料费用）
    material_price       DECIMAL(10,2),                          -- 物料单价（材料费用）
    
    -- 折旧费用相关（如果费用类型是折旧）
    equipment_id        INTEGER,                                 -- 设备ID（折旧费用）
    depreciation_period VARCHAR(20),                             -- 折旧期间（折旧费用）
    
    -- 来源信息
    source_type         VARCHAR(20),                             -- 来源类型：MANUAL/CALCULATED/ALLOCATED
    source_id           INTEGER,                                 -- 来源ID（如关联的项目成本ID）
    
    -- 分摊信息
    is_allocated        BOOLEAN DEFAULT 0,                       -- 是否分摊费用
    allocation_rule_id  INTEGER,                                 -- 分摊规则ID
    allocation_rate     DECIMAL(5,2),                            -- 分摊比例(%)
    
    -- 加计扣除
    deductible_amount   DECIMAL(12,2),                           -- 可加计扣除金额
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',            -- 状态：DRAFT/APPROVED/CANCELLED
    approved_by         INTEGER,                                 -- 审批人ID
    approved_at         DATETIME,                                -- 审批时间
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rd_project_id) REFERENCES rd_project(id),
    FOREIGN KEY (cost_type_id) REFERENCES rd_cost_type(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (allocation_rule_id) REFERENCES rd_cost_allocation_rule(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX idx_rd_cost_no ON rd_cost(cost_no);
CREATE INDEX idx_rd_cost_project ON rd_cost(rd_project_id);
CREATE INDEX idx_rd_cost_type ON rd_cost(cost_type_id);
CREATE INDEX idx_rd_cost_date ON rd_cost(cost_date);
CREATE INDEX idx_rd_cost_status ON rd_cost(status);

-- ============================================
-- 6. 研发报表记录表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_report_record (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    report_no           VARCHAR(50) NOT NULL UNIQUE,             -- 报表编号
    report_type         VARCHAR(50) NOT NULL,                   -- 报表类型：AUXILIARY_LEDGER/DEDUCTION_DETAIL/HIGH_TECH等
    report_name         VARCHAR(200) NOT NULL,                  -- 报表名称
    
    -- 报表参数
    report_params       TEXT,                                    -- 报表参数（JSON格式）
    start_date          DATE,                                    -- 开始日期
    end_date            DATE,                                    -- 结束日期
    project_ids         TEXT,                                    -- 项目ID列表（JSON）
    
    -- 生成信息
    generated_by        INTEGER NOT NULL,                        -- 生成人ID
    generated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 生成时间
    file_path           VARCHAR(500),                           -- 文件路径
    file_size           INTEGER,                                 -- 文件大小（字节）
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'GENERATED',        -- 状态：GENERATED/DOWNLOADED/ARCHIVED
    
    -- 备注
    remark              TEXT,                                   -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (generated_by) REFERENCES users(id)
);

CREATE INDEX idx_rd_report_no ON rd_report_record(report_no);
CREATE INDEX idx_rd_report_type ON rd_report_record(report_type);
CREATE INDEX idx_rd_report_date ON rd_report_record(generated_at);



