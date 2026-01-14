-- ============================================
-- 全链条分析与健康度监控模块 - MySQL 迁移文件
-- 创建日期: 2026-01-15
-- 说明: 扩展leads/opportunities/quotes/contracts表添加健康度字段，创建断链记录、健康度快照、责任记录表
-- ============================================

-- 1. 扩展leads表添加健康度字段
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS health_status VARCHAR(10) DEFAULT 'H1' COMMENT '健康度状态：H1/H2/H3/H4',
ADD COLUMN IF NOT EXISTS health_score INT COMMENT '健康度评分（0-100）',
ADD COLUMN IF NOT EXISTS last_follow_up_at DATETIME COMMENT '最后跟进时间',
ADD COLUMN IF NOT EXISTS break_risk_level VARCHAR(10) COMMENT '断链风险等级：LOW/MEDIUM/HIGH';

CREATE INDEX IF NOT EXISTS idx_leads_health_status ON leads(health_status);
CREATE INDEX IF NOT EXISTS idx_leads_break_risk ON leads(break_risk_level);

-- 2. 扩展opportunities表添加健康度字段
ALTER TABLE opportunities 
ADD COLUMN IF NOT EXISTS health_status VARCHAR(10) DEFAULT 'H1' COMMENT '健康度状态：H1/H2/H3/H4',
ADD COLUMN IF NOT EXISTS health_score INT COMMENT '健康度评分（0-100）',
ADD COLUMN IF NOT EXISTS last_progress_at DATETIME COMMENT '最后进展时间',
ADD COLUMN IF NOT EXISTS break_risk_level VARCHAR(10) COMMENT '断链风险等级：LOW/MEDIUM/HIGH';

CREATE INDEX IF NOT EXISTS idx_opportunities_health_status ON opportunities(health_status);
CREATE INDEX IF NOT EXISTS idx_opportunities_break_risk ON opportunities(break_risk_level);

-- 3. 扩展quotes表添加健康度字段
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS health_status VARCHAR(10) DEFAULT 'H1' COMMENT '健康度状态：H1/H2/H3/H4',
ADD COLUMN IF NOT EXISTS health_score INT COMMENT '健康度评分（0-100）',
ADD COLUMN IF NOT EXISTS break_risk_level VARCHAR(10) COMMENT '断链风险等级：LOW/MEDIUM/HIGH';

CREATE INDEX IF NOT EXISTS idx_quotes_health_status ON quotes(health_status);
CREATE INDEX IF NOT EXISTS idx_quotes_break_risk ON quotes(break_risk_level);

-- 4. 扩展contracts表添加健康度字段
ALTER TABLE contracts 
ADD COLUMN IF NOT EXISTS health_status VARCHAR(10) DEFAULT 'H1' COMMENT '健康度状态：H1/H2/H3/H4',
ADD COLUMN IF NOT EXISTS health_score INT COMMENT '健康度评分（0-100）',
ADD COLUMN IF NOT EXISTS break_risk_level VARCHAR(10) COMMENT '断链风险等级：LOW/MEDIUM/HIGH';

CREATE INDEX IF NOT EXISTS idx_contracts_health_status ON contracts(health_status);
CREATE INDEX IF NOT EXISTS idx_contracts_break_risk ON contracts(break_risk_level);

-- 5. 创建断链记录表
CREATE TABLE IF NOT EXISTS pipeline_break_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_id VARCHAR(50) NOT NULL COMMENT '流程ID（线索/商机/报价/合同ID）',
    pipeline_type VARCHAR(20) NOT NULL COMMENT '流程类型：LEAD/OPPORTUNITY/QUOTE/CONTRACT',
    break_stage VARCHAR(20) NOT NULL COMMENT '断链环节：LEAD_TO_OPP/OPP_TO_QUOTE/QUOTE_TO_CONTRACT/CONTRACT_TO_PROJECT/PROJECT_TO_INVOICE/INVOICE_TO_PAYMENT',
    break_reason VARCHAR(100) COMMENT '断链原因',
    break_date DATE NOT NULL COMMENT '断链日期',
    responsible_person_id INT COMMENT '责任人ID',
    responsible_department VARCHAR(50) COMMENT '责任部门',
    cost_impact DECIMAL(14,2) COMMENT '成本影响',
    opportunity_cost DECIMAL(14,2) COMMENT '机会成本',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id),
    INDEX idx_pipeline_type (pipeline_type, break_stage),
    INDEX idx_break_date (break_date),
    INDEX idx_responsible (responsible_person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='断链记录表';

-- 6. 创建健康度快照表
CREATE TABLE IF NOT EXISTS pipeline_health_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    health_status VARCHAR(10) NOT NULL COMMENT 'H1/H2/H3/H4',
    health_score INT COMMENT '健康度评分（0-100）',
    risk_factors TEXT COMMENT '风险因素JSON',
    snapshot_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pipeline (pipeline_type, pipeline_id),
    INDEX idx_snapshot_date (snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康度快照表';

-- 7. 创建责任记录表
CREATE TABLE IF NOT EXISTS accountability_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    issue_type VARCHAR(50) NOT NULL COMMENT '问题类型：DELAY/COST_OVERRUN/INFORMATION_GAP/BREAK',
    responsible_person_id INT NOT NULL,
    responsible_department VARCHAR(50),
    responsibility_ratio DECIMAL(5,2) COMMENT '责任比例（0-100）',
    cost_impact DECIMAL(14,2) COMMENT '成本影响',
    description TEXT COMMENT '责任描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id),
    INDEX idx_person (responsible_person_id),
    INDEX idx_department (responsible_department),
    INDEX idx_issue_type (issue_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='责任记录表';
