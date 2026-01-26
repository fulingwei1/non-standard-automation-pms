-- ============================================================================
-- 数据库迁移脚本: 拆分 Project 大表为多个扩展表
-- 版本: 20250122
-- 数据库: SQLite
-- ============================================================================

-- 说明: 此脚本将 Project 表的 80+ 字段拆分为多个功能模块表
-- 策略: 创建扩展表并迁移数据，保留原字段（向后兼容）

-- ============================================================================
-- 1. 创建扩展表
-- ============================================================================

-- 1.1 项目财务信息表
CREATE TABLE IF NOT EXISTS project_financials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER UNIQUE NOT NULL,
    contract_amount DECIMAL(14,2) DEFAULT 0,
    budget_amount DECIMAL(14,2) DEFAULT 0,
    actual_cost DECIMAL(14,2) DEFAULT 0,
    invoice_issued BOOLEAN DEFAULT 0,
    final_payment_completed BOOLEAN DEFAULT 0,
    final_payment_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_financials_project ON project_financials(project_id);

-- 1.2 项目ERP集成信息表
CREATE TABLE IF NOT EXISTS project_erp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER UNIQUE NOT NULL,
    erp_synced BOOLEAN DEFAULT 0,
    erp_sync_time DATETIME,
    erp_order_no VARCHAR(50),
    erp_sync_status VARCHAR(20) DEFAULT 'PENDING',
    erp_sync_error TEXT,
    erp_last_sync_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_erp_project ON project_erp(project_id);
CREATE INDEX IF NOT EXISTS idx_project_erp_status ON project_erp(erp_sync_status);

-- 1.3 项目质保信息表
CREATE TABLE IF NOT EXISTS project_warranties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER UNIQUE NOT NULL,
    warranty_period_months INTEGER,
    warranty_start_date DATE,
    warranty_end_date DATE,
    warranty_status VARCHAR(20) DEFAULT 'ACTIVE',
    warranty_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_warranties_project ON project_warranties(project_id);
CREATE INDEX IF NOT EXISTS idx_project_warranties_end_date ON project_warranties(warranty_end_date);

-- 1.4 项目实施信息表
CREATE TABLE IF NOT EXISTS project_implementations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER UNIQUE NOT NULL,
    implementation_address VARCHAR(500),
    test_encryption VARCHAR(100),
    site_contact_name VARCHAR(50),
    site_contact_phone VARCHAR(30),
    site_contact_email VARCHAR(100),
    site_conditions TEXT,
    installation_requirements TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_implementations_project ON project_implementations(project_id);

-- 1.5 项目售前评估信息表
CREATE TABLE IF NOT EXISTS project_presales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER UNIQUE NOT NULL,
    source_lead_id VARCHAR(50),
    evaluation_score DECIMAL(5,2),
    predicted_win_rate DECIMAL(5,4),
    outcome VARCHAR(20),
    loss_reason VARCHAR(50),
    loss_reason_detail TEXT,
    competitor_info TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_presales_project ON project_presales(project_id);
CREATE INDEX IF NOT EXISTS idx_project_presales_outcome ON project_presales(outcome);

-- ============================================================================
-- 2. 迁移数据从 projects 表到扩展表
-- ============================================================================

-- 2.1 迁移财务信息
INSERT INTO project_financials (
    project_id, contract_amount, budget_amount, actual_cost,
    invoice_issued, final_payment_completed, final_payment_date
)
SELECT
    id,
    contract_amount,
    budget_amount,
    actual_cost,
    invoice_issued,
    final_payment_completed,
    final_payment_date
FROM projects
WHERE contract_amount > 0 OR budget_amount > 0 OR actual_cost > 0;

-- 2.2 迁移ERP信息
INSERT INTO project_erp (
    project_id, erp_synced, erp_sync_time, erp_order_no, erp_sync_status
)
SELECT
    id,
    erp_synced,
    erp_sync_time,
    erp_order_no,
    erp_sync_status
FROM projects
WHERE erp_synced = 1 OR erp_order_no IS NOT NULL;

-- 2.3 迁移质保信息
INSERT INTO project_warranties (
    project_id, warranty_period_months, warranty_start_date, warranty_end_date
)
SELECT
    id,
    warranty_period_months,
    warranty_start_date,
    warranty_end_date
FROM projects
WHERE warranty_period_months IS NOT NULL;

-- 2.4 迁移实施信息
INSERT INTO project_implementations (
    project_id, implementation_address, test_encryption
)
SELECT
    id,
    implementation_address,
    test_encryption
FROM projects
WHERE implementation_address IS NOT NULL OR test_encryption IS NOT NULL;

-- 2.5 迁移售前评估信息
INSERT INTO project_presales (
    project_id, source_lead_id, evaluation_score, predicted_win_rate,
    outcome, loss_reason, loss_reason_detail
)
SELECT
    id,
    source_lead_id,
    evaluation_score,
    predicted_win_rate,
    outcome,
    loss_reason,
    loss_reason_detail
FROM projects
WHERE source_lead_id IS NOT NULL OR evaluation_score IS NOT NULL OR outcome IS NOT NULL;

-- ============================================================================
-- 3. 数据验证（可选）
-- ============================================================================

-- 验证数据迁移完整性
-- SELECT '项目总数' as metric, COUNT(*) as count FROM projects;
-- SELECT '财务信息迁移' as metric, COUNT(*) as count FROM project_financials;
-- SELECT 'ERP信息迁移' as metric, COUNT(*) as count FROM project_erp;
-- SELECT '质保信息迁移' as metric, COUNT(*) as count FROM project_warranties;
-- SELECT '实施信息迁移' as metric, COUNT(*) as count FROM project_implementations;
-- SELECT '售前信息迁移' as metric, COUNT(*) as count FROM project_presales;

-- ============================================================================
-- 4. 使用示例
-- ============================================================================

-- 查询项目及其财务信息（无需修改原表结构）
-- SELECT p.*, pf.contract_amount, pf.budget_amount
-- FROM projects p
-- LEFT JOIN project_financials pf ON p.id = pf.project_id
-- WHERE p.project_code = 'PJ2501001';

-- 通过 ORM 使用（Python）
-- project = session.query(Project).first()
# 通过关系访问财务信息
# if project.financial_info:
#     print(project.financial_info.is_over_budget)
# 通过便捷属性访问
# print(project.is_over_budget)

-- ============================================================================
-- 5. 回滚脚本（如果需要删除扩展表）
-- ============================================================================
-- DROP TABLE IF EXISTS project_financials;
-- DROP TABLE IF EXISTS project_erp;
-- DROP TABLE IF EXISTS project_warranties;
-- DROP TABLE IF EXISTS project_implementations;
-- DROP TABLE IF EXISTS project_presales;
