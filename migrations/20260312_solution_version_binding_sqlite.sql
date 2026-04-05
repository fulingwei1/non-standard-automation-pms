-- 方案版本和成本-报价绑定 (SQLite 版本)
-- 本迁移实现 成本-方案-报价 三位一体绑定
-- Create Date: 2026-03-12

-- ========== 1. 创建 solution_versions 表 ==========
CREATE TABLE IF NOT EXISTS solution_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id INTEGER NOT NULL,
    version_no VARCHAR(20) NOT NULL,

    -- 方案内容
    generated_solution JSON,
    architecture_diagram TEXT,
    topology_diagram TEXT,
    signal_flow_diagram TEXT,
    bom_list JSON,
    technical_parameters JSON,
    process_flow TEXT,
    solution_description TEXT,

    -- 变更信息
    change_summary TEXT,
    change_reason VARCHAR(200),
    parent_version_id INTEGER,

    -- 审批状态
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    approved_by INTEGER,
    approved_at DATETIME,
    approval_comments TEXT,

    -- AI 元数据
    ai_model_used VARCHAR(100),
    confidence_score DECIMAL(5, 4),
    quality_score DECIMAL(3, 2),

    -- 审计字段
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (solution_id) REFERENCES presale_ai_solution(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_version_id) REFERENCES solution_versions(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_sv_solution_id ON solution_versions(solution_id);
CREATE INDEX IF NOT EXISTS idx_sv_status ON solution_versions(status);
CREATE INDEX IF NOT EXISTS idx_sv_version_no ON solution_versions(solution_id, version_no);

-- ========== 2. 为 presale_ai_solution 添加 current_version_id ==========
-- SQLite 不支持直接 ADD COLUMN WITH FK，分步执行
ALTER TABLE presale_ai_solution ADD COLUMN current_version_id INTEGER;

-- ========== 3. 为 presale_ai_cost_estimation 添加字段 ==========
-- 方案版本关联
ALTER TABLE presale_ai_cost_estimation ADD COLUMN solution_version_id INTEGER;
ALTER TABLE presale_ai_cost_estimation ADD COLUMN version_no VARCHAR(20);

-- 审批流程
ALTER TABLE presale_ai_cost_estimation ADD COLUMN status VARCHAR(20) DEFAULT 'draft';
ALTER TABLE presale_ai_cost_estimation ADD COLUMN approved_by INTEGER;
ALTER TABLE presale_ai_cost_estimation ADD COLUMN approved_at DATETIME;
ALTER TABLE presale_ai_cost_estimation ADD COLUMN approval_comments TEXT;
ALTER TABLE presale_ai_cost_estimation ADD COLUMN submitted_at DATETIME;

-- 绑定标记
ALTER TABLE presale_ai_cost_estimation ADD COLUMN is_bound_to_quote INTEGER DEFAULT 0;
ALTER TABLE presale_ai_cost_estimation ADD COLUMN bound_quote_version_id INTEGER;

-- 索引
CREATE INDEX IF NOT EXISTS idx_ce_solution_version ON presale_ai_cost_estimation(solution_version_id);
CREATE INDEX IF NOT EXISTS idx_ce_status ON presale_ai_cost_estimation(status);

-- ========== 4. 为 quote_versions 添加绑定字段 ==========
ALTER TABLE quote_versions ADD COLUMN solution_version_id INTEGER;
ALTER TABLE quote_versions ADD COLUMN cost_estimation_id INTEGER;
ALTER TABLE quote_versions ADD COLUMN binding_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE quote_versions ADD COLUMN binding_validated_at DATETIME;
ALTER TABLE quote_versions ADD COLUMN binding_warning TEXT;

-- 索引
CREATE INDEX IF NOT EXISTS idx_qv_solution_version ON quote_versions(solution_version_id);
CREATE INDEX IF NOT EXISTS idx_qv_cost_estimation ON quote_versions(cost_estimation_id);
CREATE INDEX IF NOT EXISTS idx_qv_binding_status ON quote_versions(binding_status);
