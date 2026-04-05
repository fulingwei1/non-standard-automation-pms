-- 技术评估工作流和销售漏斗状态机数据库迁移
-- 日期: 2026-03-12
-- 适用: SQLite

-- ===================================================
-- 第一部分：技术评估模板和工作流
-- ===================================================

-- 评估模板表
CREATE TABLE IF NOT EXISTS assessment_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,
    template_name VARCHAR(200) NOT NULL,
    category VARCHAR(20) DEFAULT 'STANDARD',
    description TEXT,
    dimension_weights TEXT, -- JSON
    veto_rules TEXT, -- JSON
    score_thresholds TEXT, -- JSON
    version VARCHAR(20) DEFAULT 'V1.0',
    is_active BOOLEAN DEFAULT 1,
    is_default BOOLEAN DEFAULT 0,
    approved_by INTEGER REFERENCES users(id),
    approved_at DATETIME,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assessment_template_code ON assessment_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_assessment_template_category ON assessment_templates(category);
CREATE INDEX IF NOT EXISTS idx_assessment_template_active ON assessment_templates(is_active);

-- 评估项表
CREATE TABLE IF NOT EXISTS assessment_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES assessment_templates(id),
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    dimension VARCHAR(20) NOT NULL,
    description TEXT,
    max_score INTEGER DEFAULT 10,
    weight DECIMAL(5,2) DEFAULT 1.0,
    scoring_criteria TEXT, -- JSON
    is_veto_item BOOLEAN DEFAULT 0,
    veto_threshold INTEGER,
    is_required BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, item_code)
);

CREATE INDEX IF NOT EXISTS idx_assessment_item_template ON assessment_items(template_id);
CREATE INDEX IF NOT EXISTS idx_assessment_item_dimension ON assessment_items(dimension);

-- 评估风险记录表
CREATE TABLE IF NOT EXISTS assessment_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL REFERENCES technical_assessments(id),
    risk_code VARCHAR(50) NOT NULL UNIQUE,
    risk_title VARCHAR(200) NOT NULL,
    risk_category VARCHAR(50),
    risk_description TEXT NOT NULL,
    probability VARCHAR(10),
    impact VARCHAR(10),
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    risk_score INTEGER,
    mitigation_plan TEXT,
    contingency_plan TEXT,
    owner_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'OPEN',
    due_date DATETIME,
    resolved_at DATETIME,
    resolution_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assessment_risk_assessment ON assessment_risks(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_risk_level ON assessment_risks(risk_level);
CREATE INDEX IF NOT EXISTS idx_assessment_risk_status ON assessment_risks(status);
CREATE INDEX IF NOT EXISTS idx_assessment_risk_owner ON assessment_risks(owner_id);

-- 评估版本表
CREATE TABLE IF NOT EXISTS assessment_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL REFERENCES technical_assessments(id),
    version_no VARCHAR(20) NOT NULL,
    version_note TEXT,
    snapshot_data TEXT, -- JSON
    dimension_scores TEXT, -- JSON
    total_score INTEGER,
    decision VARCHAR(30),
    evaluator_id INTEGER REFERENCES users(id),
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, version_no)
);

CREATE INDEX IF NOT EXISTS idx_assessment_version_assessment ON assessment_versions(assessment_id);

-- 扩展 technical_assessments 表
-- 注意: SQLite 不支持 ADD COLUMN IF NOT EXISTS，需要检查列是否存在
-- 如果列不存在则添加

-- presale_ticket_id
SELECT 1 FROM pragma_table_info('technical_assessments') WHERE name='presale_ticket_id'
UNION ALL SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM pragma_table_info('technical_assessments') WHERE name='presale_ticket_id');

-- 使用 Python/Alembic 执行以下迁移会更安全
-- ALTER TABLE technical_assessments ADD COLUMN presale_ticket_id INTEGER REFERENCES presale_support_ticket(id);
-- ALTER TABLE technical_assessments ADD COLUMN template_id INTEGER REFERENCES assessment_templates(id);
-- ALTER TABLE technical_assessments ADD COLUMN version_no VARCHAR(20) DEFAULT 'V1.0';
-- ALTER TABLE technical_assessments ADD COLUMN is_latest BOOLEAN DEFAULT 1;
-- ALTER TABLE technical_assessments ADD COLUMN previous_version_id INTEGER REFERENCES technical_assessments(id);
-- ALTER TABLE technical_assessments ADD COLUMN item_scores TEXT;

-- ===================================================
-- 第二部分：销售漏斗状态机
-- ===================================================

-- 漏斗阶段定义表
CREATE TABLE IF NOT EXISTS sales_funnel_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_code VARCHAR(50) NOT NULL UNIQUE,
    stage_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    sequence INTEGER NOT NULL,
    description TEXT,
    color VARCHAR(20),
    icon VARCHAR(50),
    default_probability INTEGER DEFAULT 0,
    allowed_next_stages TEXT, -- JSON
    required_gate VARCHAR(10),
    is_active BOOLEAN DEFAULT 1,
    is_terminal BOOLEAN DEFAULT 0,
    is_won BOOLEAN DEFAULT 0,
    is_lost BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, sequence)
);

CREATE INDEX IF NOT EXISTS idx_funnel_stage_entity ON sales_funnel_stages(entity_type);
CREATE INDEX IF NOT EXISTS idx_funnel_stage_sequence ON sales_funnel_stages(sequence);

-- 阶段门配置表
CREATE TABLE IF NOT EXISTS stage_gate_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_type VARCHAR(10) NOT NULL UNIQUE,
    gate_name VARCHAR(100) NOT NULL,
    description TEXT,
    validation_rules TEXT, -- JSON
    required_fields TEXT, -- JSON
    required_documents TEXT, -- JSON
    requires_approval BOOLEAN DEFAULT 0,
    approval_roles TEXT, -- JSON
    notification_config TEXT, -- JSON
    is_active BOOLEAN DEFAULT 1,
    can_be_waived BOOLEAN DEFAULT 0,
    waive_approval_roles TEXT, -- JSON
    version VARCHAR(20) DEFAULT 'V1.0',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gate_config_type ON stage_gate_configs(gate_type);

-- 阶段门验证结果表
CREATE TABLE IF NOT EXISTS stage_gate_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    gate_type VARCHAR(10) NOT NULL,
    result VARCHAR(20) DEFAULT 'PENDING',
    validation_details TEXT, -- JSON
    passed_rules TEXT, -- JSON
    failed_rules TEXT, -- JSON
    warnings TEXT, -- JSON
    score INTEGER,
    threshold INTEGER,
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    validated_by INTEGER REFERENCES users(id),
    is_waived BOOLEAN DEFAULT 0,
    waived_by INTEGER REFERENCES users(id),
    waived_at DATETIME,
    waive_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gate_result_entity ON stage_gate_results(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_gate_result_gate ON stage_gate_results(gate_type);
CREATE INDEX IF NOT EXISTS idx_gate_result_result ON stage_gate_results(result);

-- 阶段滞留时间配置表
CREATE TABLE IF NOT EXISTS stage_dwell_time_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id INTEGER NOT NULL UNIQUE REFERENCES sales_funnel_stages(id),
    expected_hours INTEGER NOT NULL,
    warning_hours INTEGER,
    critical_hours INTEGER,
    amount_thresholds TEXT, -- JSON
    customer_level_config TEXT, -- JSON
    alert_enabled BOOLEAN DEFAULT 1,
    alert_recipients TEXT, -- JSON
    escalation_config TEXT, -- JSON
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dwell_config_stage ON stage_dwell_time_configs(stage_id);

-- 滞留时间告警记录表
CREATE TABLE IF NOT EXISTS stage_dwell_time_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    stage_id INTEGER NOT NULL REFERENCES sales_funnel_stages(id),
    alert_code VARCHAR(50) NOT NULL UNIQUE,
    severity VARCHAR(20) DEFAULT 'WARNING',
    alert_message TEXT,
    entered_stage_at DATETIME,
    dwell_hours INTEGER,
    threshold_hours INTEGER,
    amount DECIMAL(15,2),
    owner_id INTEGER REFERENCES users(id),
    owner_name VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at DATETIME,
    resolved_at DATETIME,
    resolution_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dwell_alert_entity ON stage_dwell_time_alerts(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_dwell_alert_stage ON stage_dwell_time_alerts(stage_id);
CREATE INDEX IF NOT EXISTS idx_dwell_alert_status ON stage_dwell_time_alerts(status);
CREATE INDEX IF NOT EXISTS idx_dwell_alert_severity ON stage_dwell_time_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_dwell_alert_owner ON stage_dwell_time_alerts(owner_id);

-- 漏斗状态转换日志表
CREATE TABLE IF NOT EXISTS funnel_transition_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    entity_code VARCHAR(50),
    from_stage VARCHAR(50),
    to_stage VARCHAR(50),
    gate_type VARCHAR(10),
    gate_result_id INTEGER REFERENCES stage_gate_results(id),
    transition_reason TEXT,
    transitioned_by INTEGER REFERENCES users(id),
    transitioned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    extra_data TEXT, -- JSON
    dwell_hours INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transition_log_entity ON funnel_transition_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_transition_log_time ON funnel_transition_logs(transitioned_at);
CREATE INDEX IF NOT EXISTS idx_transition_log_from ON funnel_transition_logs(from_stage);
CREATE INDEX IF NOT EXISTS idx_transition_log_to ON funnel_transition_logs(to_stage);

-- 漏斗统计快照表
CREATE TABLE IF NOT EXISTS funnel_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date DATETIME NOT NULL,
    snapshot_type VARCHAR(20) DEFAULT 'DAILY',
    stage_counts TEXT, -- JSON
    stage_amounts TEXT, -- JSON
    conversion_rates TEXT, -- JSON
    dwell_stats TEXT, -- JSON
    forecast_data TEXT, -- JSON
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_funnel_snapshot_date ON funnel_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_funnel_snapshot_type ON funnel_snapshots(snapshot_type);

-- ===================================================
-- 第三部分：初始化数据
-- ===================================================

-- 初始化阶段门配置
INSERT OR IGNORE INTO stage_gate_configs (gate_type, gate_name, description, validation_rules, is_active)
VALUES
    ('G1', 'G1 线索转商机', '验证线索是否具备转商机条件', '{"pass_threshold": 60}', 1),
    ('G2', 'G2 商机转报价', '验证商机是否具备报价条件', '{"pass_threshold": 70}', 1),
    ('G3', 'G3 报价转合同', '验证报价是否具备签约条件', '{"pass_threshold": 75, "min_margin_rate": 15}', 1),
    ('G4', 'G4 合同转项目', '验证合同是否具备立项条件', '{"pass_threshold": 80}', 1);

-- 初始化漏斗阶段定义（线索）
INSERT OR IGNORE INTO sales_funnel_stages (stage_code, stage_name, entity_type, sequence, default_probability, allowed_next_stages, required_gate)
VALUES
    ('LEAD_NEW', '新线索', 'LEAD', 1, 5, '["LEAD_CONTACTED", "LEAD_LOST"]', NULL),
    ('LEAD_CONTACTED', '已联系', 'LEAD', 2, 10, '["LEAD_QUALIFIED", "LEAD_LOST"]', NULL),
    ('LEAD_QUALIFIED', '已合格', 'LEAD', 3, 20, '["CONVERTED", "LEAD_LOST"]', 'G1'),
    ('CONVERTED', '已转化', 'LEAD', 4, 30, '[]', NULL),
    ('LEAD_LOST', '已丢失', 'LEAD', 5, 0, '[]', NULL);

-- 初始化漏斗阶段定义（商机）
INSERT OR IGNORE INTO sales_funnel_stages (stage_code, stage_name, entity_type, sequence, default_probability, allowed_next_stages, required_gate)
VALUES
    ('DISCOVERY', '初步接触', 'OPPORTUNITY', 1, 10, '["QUALIFICATION", "LOST", "ON_HOLD"]', NULL),
    ('QUALIFICATION', '需求挖掘', 'OPPORTUNITY', 2, 30, '["PROPOSAL", "LOST", "ON_HOLD"]', 'G2'),
    ('PROPOSAL', '方案介绍', 'OPPORTUNITY', 3, 50, '["NEGOTIATION", "LOST", "ON_HOLD"]', NULL),
    ('NEGOTIATION', '价格谈判', 'OPPORTUNITY', 4, 70, '["WON", "LOST", "ON_HOLD"]', NULL),
    ('WON', '赢单', 'OPPORTUNITY', 5, 100, '[]', NULL),
    ('LOST', '输单', 'OPPORTUNITY', 6, 0, '[]', NULL),
    ('ON_HOLD', '暂停', 'OPPORTUNITY', 7, 0, '["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]', NULL);

-- 初始化默认评估模板
INSERT OR IGNORE INTO assessment_templates (template_code, template_name, category, description, dimension_weights, score_thresholds, is_default, is_active)
VALUES (
    'TPL_DEFAULT_STANDARD',
    '标准设备评估模板',
    'STANDARD',
    '适用于标准自动化设备项目的技术评估',
    '{"TECHNICAL": 30, "COMMERCIAL": 25, "RESOURCE": 15, "RISK": 20, "TIMELINE": 10}',
    '{"excellent": 90, "good": 75, "fair": 60, "poor": 0}',
    1,
    1
);

-- 为默认模板添加评估项
INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, sort_order)
SELECT
    t.id,
    'TECH_FEASIBILITY',
    '技术可行性',
    'TECHNICAL',
    10,
    1.5,
    '评估项目技术方案的可行性',
    1
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, sort_order)
SELECT
    t.id,
    'TECH_COMPLEXITY',
    '技术复杂度',
    'TECHNICAL',
    10,
    1.0,
    '评估项目技术实现的复杂程度',
    2
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, sort_order)
SELECT
    t.id,
    'COMM_PROFIT',
    '预期利润',
    'COMMERCIAL',
    10,
    1.5,
    '评估项目的盈利预期',
    3
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, sort_order)
SELECT
    t.id,
    'RES_AVAILABLE',
    '资源可用性',
    'RESOURCE',
    10,
    1.0,
    '评估实施所需资源的可用性',
    4
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, is_veto_item, veto_threshold, sort_order)
SELECT
    t.id,
    'RISK_OVERALL',
    '整体风险',
    'RISK',
    10,
    1.5,
    '评估项目整体风险水平（一票否决项）',
    1,
    3,
    5
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

INSERT OR IGNORE INTO assessment_items (template_id, item_code, item_name, dimension, max_score, weight, description, sort_order)
SELECT
    t.id,
    'TIME_DELIVERY',
    '交付周期',
    'TIMELINE',
    10,
    1.0,
    '评估项目交付周期的合理性',
    6
FROM assessment_templates t WHERE t.template_code = 'TPL_DEFAULT_STANDARD';

-- ===================================================
-- 完成
-- ===================================================
