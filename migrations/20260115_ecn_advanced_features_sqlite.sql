-- ECN高级功能扩展 - SQLite版本
-- 添加BOM影响分析、责任分摊、RCA分析等功能

-- 1. 扩展EcnAffectedMaterial表，添加BOM影响范围和呆滞料相关字段
ALTER TABLE ecn_affected_materials ADD COLUMN bom_impact_scope TEXT;
ALTER TABLE ecn_affected_materials ADD COLUMN is_obsolete_risk BOOLEAN DEFAULT 0;
ALTER TABLE ecn_affected_materials ADD COLUMN obsolete_risk_level VARCHAR(20);
ALTER TABLE ecn_affected_materials ADD COLUMN obsolete_quantity NUMERIC(10, 4);
ALTER TABLE ecn_affected_materials ADD COLUMN obsolete_cost NUMERIC(14, 2);
ALTER TABLE ecn_affected_materials ADD COLUMN obsolete_analysis TEXT;

-- 2. 扩展Ecn表，添加RCA分析和解决方案字段
ALTER TABLE ecn ADD COLUMN root_cause VARCHAR(20);
ALTER TABLE ecn ADD COLUMN root_cause_analysis TEXT;
ALTER TABLE ecn ADD COLUMN root_cause_category VARCHAR(50);
ALTER TABLE ecn ADD COLUMN solution TEXT;
ALTER TABLE ecn ADD COLUMN solution_template_id INTEGER;
ALTER TABLE ecn ADD COLUMN similar_ecn_ids TEXT;
ALTER TABLE ecn ADD COLUMN solution_source VARCHAR(20);

-- 3. 创建ECN BOM影响分析表
CREATE TABLE IF NOT EXISTS ecn_bom_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id INTEGER NOT NULL,
    bom_version_id INTEGER,
    machine_id INTEGER,
    project_id INTEGER,
    affected_item_count INTEGER DEFAULT 0,
    total_cost_impact NUMERIC(14, 2) DEFAULT 0,
    schedule_impact_days INTEGER DEFAULT 0,
    impact_analysis TEXT,
    analysis_status VARCHAR(20) DEFAULT 'PENDING',
    analyzed_at DATETIME,
    analyzed_by INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (bom_version_id) REFERENCES bom_headers(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analyzed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bom_impact_ecn ON ecn_bom_impacts(ecn_id);
CREATE INDEX IF NOT EXISTS idx_bom_impact_bom ON ecn_bom_impacts(bom_version_id);
CREATE INDEX IF NOT EXISTS idx_bom_impact_machine ON ecn_bom_impacts(machine_id);

-- 4. 创建ECN责任分摊表
CREATE TABLE IF NOT EXISTS ecn_responsibilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id INTEGER NOT NULL,
    dept VARCHAR(50) NOT NULL,
    responsibility_ratio NUMERIC(5, 2) DEFAULT 0,
    responsibility_type VARCHAR(20) DEFAULT 'PRIMARY',
    cost_allocation NUMERIC(14, 2) DEFAULT 0,
    impact_description TEXT,
    responsibility_scope TEXT,
    confirmed BOOLEAN DEFAULT 0,
    confirmed_by INTEGER,
    confirmed_at DATETIME,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_resp_ecn ON ecn_responsibilities(ecn_id);
CREATE INDEX IF NOT EXISTS idx_resp_dept ON ecn_responsibilities(dept);
