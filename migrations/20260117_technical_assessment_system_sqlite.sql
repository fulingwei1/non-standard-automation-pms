-- Technical Assessment System migration (SQLite)
-- Targets: technical_assessments/scoring_rules/failure_cases/lead_requirement_details/requirement_freezes/open_items/ai_clarifications
-- Extends: leads/opportunities tables

-- PRAGMA foreign_keys = ON;  -- Disabled for migration
BEGIN;

-- 1) Technical Assessments
CREATE TABLE IF NOT EXISTS technical_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    evaluator_id INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',
    total_score INTEGER,
    dimension_scores TEXT,
    veto_triggered BOOLEAN DEFAULT 0,
    veto_rules TEXT,
    decision VARCHAR(30),
    risks TEXT,
    similar_cases TEXT,
    ai_analysis TEXT,
    conditions TEXT,
    evaluated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_assessment_source ON technical_assessments(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_assessment_status ON technical_assessments(status);
CREATE INDEX IF NOT EXISTS idx_assessment_evaluator ON technical_assessments(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_assessment_decision ON technical_assessments(decision);

-- 2) Scoring Rules
CREATE TABLE IF NOT EXISTS scoring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(20) UNIQUE NOT NULL,
    rules_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 0,
    description TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_scoring_rule_active ON scoring_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_scoring_rule_version ON scoring_rules(version);

-- 3) Failure Cases
CREATE TABLE IF NOT EXISTS failure_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    industry VARCHAR(50) NOT NULL,
    product_types TEXT,
    processes TEXT,
    takt_time_s INTEGER,
    annual_volume INTEGER,
    budget_status VARCHAR(50),
    customer_project_status VARCHAR(50),
    spec_status VARCHAR(50),
    price_sensitivity VARCHAR(50),
    delivery_months INTEGER,
    failure_tags TEXT NOT NULL,
    core_failure_reason TEXT NOT NULL,
    early_warning_signals TEXT NOT NULL,
    final_result VARCHAR(100),
    lesson_learned TEXT NOT NULL,
    keywords TEXT NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_failure_case_industry ON failure_cases(industry);
CREATE INDEX IF NOT EXISTS idx_failure_case_code ON failure_cases(case_code);

-- 4) Lead Requirement Details
CREATE TABLE IF NOT EXISTS lead_requirement_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    customer_factory_location VARCHAR(200),
    target_object_type VARCHAR(100),
    application_scenario VARCHAR(100),
    delivery_mode VARCHAR(100),
    expected_delivery_date DATETIME,
    requirement_source VARCHAR(100),
    participant_ids TEXT,
    requirement_maturity INTEGER,
    has_sow BOOLEAN,
    has_interface_doc BOOLEAN,
    has_drawing_doc BOOLEAN,
    sample_availability TEXT,
    customer_support_resources TEXT,
    key_risk_factors TEXT,
    veto_triggered BOOLEAN DEFAULT 0,
    veto_reason TEXT,
    target_capacity_uph DECIMAL(10,2),
    target_capacity_daily DECIMAL(10,2),
    target_capacity_shift DECIMAL(10,2),
    cycle_time_seconds DECIMAL(10,2),
    workstation_count INTEGER,
    changeover_method VARCHAR(100),
    yield_target DECIMAL(5,2),
    retest_allowed BOOLEAN,
    retest_max_count INTEGER,
    traceability_type VARCHAR(50),
    data_retention_period INTEGER,
    data_format VARCHAR(100),
    test_scope TEXT,
    key_metrics_spec TEXT,
    coverage_boundary TEXT,
    exception_handling TEXT,
    acceptance_method VARCHAR(100),
    acceptance_basis TEXT,
    delivery_checklist TEXT,
    interface_types TEXT,
    io_point_estimate TEXT,
    communication_protocols TEXT,
    upper_system_integration TEXT,
    data_field_list TEXT,
    it_security_restrictions TEXT,
    power_supply TEXT,
    air_supply TEXT,
    environment TEXT,
    safety_requirements TEXT,
    space_and_logistics TEXT,
    customer_site_standards TEXT,
    customer_supplied_materials TEXT,
    restricted_brands TEXT,
    specified_brands TEXT,
    long_lead_items TEXT,
    spare_parts_requirement TEXT,
    after_sales_support TEXT,
    requirement_version VARCHAR(50),
    is_frozen BOOLEAN DEFAULT 0,
    frozen_at DATETIME,
    frozen_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (frozen_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_detail_lead ON lead_requirement_details(lead_id);
CREATE INDEX IF NOT EXISTS idx_requirement_detail_frozen ON lead_requirement_details(is_frozen);

-- 5) Requirement Freezes
CREATE TABLE IF NOT EXISTS requirement_freezes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    freeze_type VARCHAR(50) NOT NULL,
    freeze_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    frozen_by INTEGER NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    requires_ecr BOOLEAN DEFAULT 1,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frozen_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_freeze_source ON requirement_freezes(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_requirement_freeze_type ON requirement_freezes(freeze_type);
CREATE INDEX IF NOT EXISTS idx_requirement_freeze_time ON requirement_freezes(freeze_time);

-- 6) Open Items
CREATE TABLE IF NOT EXISTS open_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    responsible_party VARCHAR(50) NOT NULL,
    responsible_person_id INTEGER,
    due_date DATETIME,
    status VARCHAR(20) DEFAULT 'PENDING',
    close_evidence TEXT,
    blocks_quotation BOOLEAN DEFAULT 0,
    closed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_open_item_source ON open_items(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_open_item_status ON open_items(status);
CREATE INDEX IF NOT EXISTS idx_open_item_type ON open_items(item_type);
CREATE INDEX IF NOT EXISTS idx_open_item_blocks ON open_items(blocks_quotation);
CREATE INDEX IF NOT EXISTS idx_open_item_due_date ON open_items(due_date);

-- 7) AI Clarifications
CREATE TABLE IF NOT EXISTS ai_clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    round INTEGER NOT NULL,
    questions TEXT NOT NULL,
    answers TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_clarification_source ON ai_clarifications(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_ai_clarification_round ON ai_clarifications(round);

-- 8) Extend leads table
ALTER TABLE leads ADD COLUMN requirement_detail_id INTEGER;
ALTER TABLE leads ADD COLUMN assessment_id INTEGER;
ALTER TABLE leads ADD COLUMN completeness INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN assignee_id INTEGER;
ALTER TABLE leads ADD COLUMN assessment_status VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_lead_assessment ON leads(assessment_id);
CREATE INDEX IF NOT EXISTS idx_lead_assignee ON leads(assignee_id);

-- 9) Extend opportunities table
ALTER TABLE opportunities ADD COLUMN assessment_id INTEGER;
ALTER TABLE opportunities ADD COLUMN requirement_maturity INTEGER;
ALTER TABLE opportunities ADD COLUMN assessment_status VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_opportunity_assessment ON opportunities(assessment_id);

COMMIT;






