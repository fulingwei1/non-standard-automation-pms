-- ============================================
-- 全链条分析与健康度监控模块 - SQLite 迁移文件
-- 创建日期: 2026-01-15
-- 说明: 扩展leads/opportunities/quotes/contracts表添加健康度字段，创建断链记录、健康度快照、责任记录表
-- ============================================

-- 1. 扩展leads表添加健康度字段
ALTER TABLE leads 
ADD COLUMN health_status VARCHAR(10) DEFAULT 'H1';

ALTER TABLE leads 
ADD COLUMN health_score INT;

ALTER TABLE leads 
ADD COLUMN last_follow_up_at DATETIME;

ALTER TABLE leads 
ADD COLUMN break_risk_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_leads_health_status ON leads(health_status);
CREATE INDEX IF NOT EXISTS idx_leads_break_risk ON leads(break_risk_level);

-- 2. 扩展opportunities表添加健康度字段
ALTER TABLE opportunities 
ADD COLUMN health_status VARCHAR(10) DEFAULT 'H1';

ALTER TABLE opportunities 
ADD COLUMN health_score INT;

ALTER TABLE opportunities 
ADD COLUMN last_progress_at DATETIME;

ALTER TABLE opportunities 
ADD COLUMN break_risk_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_opportunities_health_status ON opportunities(health_status);
CREATE INDEX IF NOT EXISTS idx_opportunities_break_risk ON opportunities(break_risk_level);

-- 3. 扩展quotes表添加健康度字段
ALTER TABLE quotes 
ADD COLUMN health_status VARCHAR(10) DEFAULT 'H1';

ALTER TABLE quotes 
ADD COLUMN health_score INT;

ALTER TABLE quotes 
ADD COLUMN break_risk_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_quotes_health_status ON quotes(health_status);
CREATE INDEX IF NOT EXISTS idx_quotes_break_risk ON quotes(break_risk_level);

-- 4. 扩展contracts表添加健康度字段
ALTER TABLE contracts 
ADD COLUMN health_status VARCHAR(10) DEFAULT 'H1';

ALTER TABLE contracts 
ADD COLUMN health_score INT;

ALTER TABLE contracts 
ADD COLUMN break_risk_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_contracts_health_status ON contracts(health_status);
CREATE INDEX IF NOT EXISTS idx_contracts_break_risk ON contracts(break_risk_level);

-- 5. 创建断链记录表
CREATE TABLE IF NOT EXISTS pipeline_break_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    break_stage VARCHAR(20) NOT NULL,
    break_reason VARCHAR(100),
    break_date DATE NOT NULL,
    responsible_person_id INTEGER,
    responsible_department VARCHAR(50),
    cost_impact DECIMAL(14,2),
    opportunity_cost DECIMAL(14,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_type ON pipeline_break_records(pipeline_type, break_stage);
CREATE INDEX IF NOT EXISTS idx_break_date ON pipeline_break_records(break_date);
CREATE INDEX IF NOT EXISTS idx_responsible ON pipeline_break_records(responsible_person_id);

-- 6. 创建健康度快照表
CREATE TABLE IF NOT EXISTS pipeline_health_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    health_status VARCHAR(10) NOT NULL,
    health_score INT,
    risk_factors TEXT,
    snapshot_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline ON pipeline_health_snapshots(pipeline_type, pipeline_id);
CREATE INDEX IF NOT EXISTS idx_snapshot_date ON pipeline_health_snapshots(snapshot_date);

-- 7. 创建责任记录表
CREATE TABLE IF NOT EXISTS accountability_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    responsible_person_id INTEGER NOT NULL,
    responsible_department VARCHAR(50),
    responsibility_ratio DECIMAL(5,2),
    cost_impact DECIMAL(14,2),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_person ON accountability_records(responsible_person_id);
CREATE INDEX IF NOT EXISTS idx_department ON accountability_records(responsible_department);
CREATE INDEX IF NOT EXISTS idx_issue_type ON accountability_records(issue_type);
