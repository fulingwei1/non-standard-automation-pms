-- Technical Assessment System migration (MySQL 8+)
-- Targets: technical_assessments/scoring_rules/failure_cases/lead_requirement_details/requirement_freezes/open_items/ai_clarifications
-- Extends: leads/opportunities tables

-- 1) Technical Assessments
CREATE TABLE IF NOT EXISTS technical_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL COMMENT '来源类型：LEAD/OPPORTUNITY',
    source_id INT NOT NULL COMMENT '来源ID',
    evaluator_id INT COMMENT '评估人ID',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '评估状态',
    total_score INT COMMENT '总分',
    dimension_scores TEXT COMMENT '五维分数详情(JSON)',
    veto_triggered BOOLEAN DEFAULT FALSE COMMENT '是否触发一票否决',
    veto_rules TEXT COMMENT '触发的否决规则(JSON)',
    decision VARCHAR(30) COMMENT '决策建议',
    risks TEXT COMMENT '风险列表(JSON)',
    similar_cases TEXT COMMENT '相似失败案例(JSON)',
    ai_analysis TEXT COMMENT 'AI分析报告',
    conditions TEXT COMMENT '立项条件(JSON)',
    evaluated_at DATETIME COMMENT '评估完成时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_assessment_source (source_type, source_id),
    INDEX idx_assessment_status (status),
    INDEX idx_assessment_evaluator (evaluator_id),
    INDEX idx_assessment_decision (decision),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技术评估结果表';

-- 2) Scoring Rules
CREATE TABLE IF NOT EXISTS scoring_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(20) UNIQUE NOT NULL COMMENT '版本号',
    rules_json TEXT NOT NULL COMMENT '完整规则配置(JSON)',
    is_active BOOLEAN DEFAULT FALSE COMMENT '是否启用',
    description TEXT COMMENT '描述',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_scoring_rule_active (is_active),
    INDEX idx_scoring_rule_version (version),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评分规则配置表';

-- 3) Failure Cases
CREATE TABLE IF NOT EXISTS failure_cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_code VARCHAR(50) UNIQUE NOT NULL COMMENT '案例编号',
    project_name VARCHAR(200) NOT NULL COMMENT '项目名称',
    industry VARCHAR(50) NOT NULL COMMENT '行业',
    product_types TEXT COMMENT '产品类型(JSON Array)',
    processes TEXT COMMENT '工序/测试类型(JSON Array)',
    takt_time_s INT COMMENT '节拍时间(秒)',
    annual_volume INT COMMENT '年产量',
    budget_status VARCHAR(50) COMMENT '预算状态',
    customer_project_status VARCHAR(50) COMMENT '客户项目状态',
    spec_status VARCHAR(50) COMMENT '规范状态',
    price_sensitivity VARCHAR(50) COMMENT '价格敏感度',
    delivery_months INT COMMENT '交付周期(月)',
    failure_tags TEXT NOT NULL COMMENT '失败标签(JSON Array)',
    core_failure_reason TEXT NOT NULL COMMENT '核心失败原因',
    early_warning_signals TEXT NOT NULL COMMENT '预警信号(JSON Array)',
    final_result VARCHAR(100) COMMENT '最终结果',
    lesson_learned TEXT NOT NULL COMMENT '教训总结',
    keywords TEXT NOT NULL COMMENT '关键词(JSON Array)',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_failure_case_industry (industry),
    INDEX idx_failure_case_code (case_code),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='失败案例库表';

-- 4) Lead Requirement Details
CREATE TABLE IF NOT EXISTS lead_requirement_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lead_id INT NOT NULL COMMENT '线索ID',
    customer_factory_location VARCHAR(200) COMMENT '客户工厂/地点',
    target_object_type VARCHAR(100) COMMENT '被测对象类型',
    application_scenario VARCHAR(100) COMMENT '应用场景',
    delivery_mode VARCHAR(100) COMMENT '计划交付模式',
    expected_delivery_date DATETIME COMMENT '期望交付日期',
    requirement_source VARCHAR(100) COMMENT '需求来源',
    participant_ids TEXT COMMENT '参与人员(JSON Array)',
    requirement_maturity INT COMMENT '需求成熟度(1-5级)',
    has_sow BOOLEAN COMMENT '是否有客户SOW/URS',
    has_interface_doc BOOLEAN COMMENT '是否有接口协议文档',
    has_drawing_doc BOOLEAN COMMENT '是否有图纸/原理/IO清单',
    sample_availability TEXT COMMENT '样品可提供情况(JSON)',
    customer_support_resources TEXT COMMENT '客户配合资源(JSON)',
    key_risk_factors TEXT COMMENT '关键风险初判(JSON Array)',
    veto_triggered BOOLEAN DEFAULT FALSE COMMENT '一票否决触发',
    veto_reason TEXT COMMENT '一票否决原因',
    target_capacity_uph DECIMAL(10,2) COMMENT '目标产能(UPH)',
    target_capacity_daily DECIMAL(10,2) COMMENT '目标产能(日)',
    target_capacity_shift DECIMAL(10,2) COMMENT '目标产能(班)',
    cycle_time_seconds DECIMAL(10,2) COMMENT '节拍要求(CT秒)',
    workstation_count INT COMMENT '工位数/并行数',
    changeover_method VARCHAR(100) COMMENT '换型方式',
    yield_target DECIMAL(5,2) COMMENT '良率目标',
    retest_allowed BOOLEAN COMMENT '是否允许复测',
    retest_max_count INT COMMENT '复测次数',
    traceability_type VARCHAR(50) COMMENT '追溯要求',
    data_retention_period INT COMMENT '数据保留期限(天)',
    data_format VARCHAR(100) COMMENT '数据格式',
    test_scope TEXT COMMENT '测试范围(JSON Array)',
    key_metrics_spec TEXT COMMENT '关键指标口径(JSON)',
    coverage_boundary TEXT COMMENT '覆盖边界(JSON)',
    exception_handling TEXT COMMENT '允许的异常处理(JSON)',
    acceptance_method VARCHAR(100) COMMENT '验收方式',
    acceptance_basis TEXT COMMENT '验收依据',
    delivery_checklist TEXT COMMENT '验收交付物清单(JSON Array)',
    interface_types TEXT COMMENT '被测对象接口类型(JSON Array)',
    io_point_estimate TEXT COMMENT 'IO点数估算(JSON)',
    communication_protocols TEXT COMMENT '通讯协议(JSON Array)',
    upper_system_integration TEXT COMMENT '与上位系统对接(JSON)',
    data_field_list TEXT COMMENT '数据字段清单(JSON Array)',
    it_security_restrictions TEXT COMMENT 'IT安全/网络限制(JSON)',
    power_supply TEXT COMMENT '供电(JSON)',
    air_supply TEXT COMMENT '气源(JSON)',
    environment TEXT COMMENT '环境(JSON)',
    safety_requirements TEXT COMMENT '安全要求(JSON)',
    space_and_logistics TEXT COMMENT '占地与物流(JSON)',
    customer_site_standards TEXT COMMENT '客户现场规范(JSON)',
    customer_supplied_materials TEXT COMMENT '客供物料清单(JSON Array)',
    restricted_brands TEXT COMMENT '禁用品牌(JSON Array)',
    specified_brands TEXT COMMENT '指定品牌(JSON Array)',
    long_lead_items TEXT COMMENT '长周期件提示(JSON Array)',
    spare_parts_requirement TEXT COMMENT '备品备件要求(JSON)',
    after_sales_support TEXT COMMENT '售后支持要求(JSON)',
    requirement_version VARCHAR(50) COMMENT '需求包版本号',
    is_frozen BOOLEAN DEFAULT FALSE COMMENT '是否冻结',
    frozen_at DATETIME COMMENT '冻结时间',
    frozen_by INT COMMENT '冻结人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_requirement_detail_lead (lead_id),
    INDEX idx_requirement_detail_frozen (is_frozen),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (frozen_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='线索需求详情表';

-- 5) Requirement Freezes
CREATE TABLE IF NOT EXISTS requirement_freezes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL COMMENT '来源类型：LEAD/OPPORTUNITY',
    source_id INT NOT NULL COMMENT '来源ID',
    freeze_type VARCHAR(50) NOT NULL COMMENT '冻结点类型',
    freeze_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '冻结时间',
    frozen_by INT NOT NULL COMMENT '冻结人ID',
    version_number VARCHAR(50) NOT NULL COMMENT '冻结版本号',
    requires_ecr BOOLEAN DEFAULT TRUE COMMENT '冻结后变更是否必须走ECR/ECN',
    description TEXT COMMENT '冻结说明',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_requirement_freeze_source (source_type, source_id),
    INDEX idx_requirement_freeze_type (freeze_type),
    INDEX idx_requirement_freeze_time (freeze_time),
    FOREIGN KEY (frozen_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='需求冻结记录表';

-- 6) Open Items
CREATE TABLE IF NOT EXISTS open_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL COMMENT '来源类型：LEAD/OPPORTUNITY',
    source_id INT NOT NULL COMMENT '来源ID',
    item_code VARCHAR(50) UNIQUE NOT NULL COMMENT '未决事项编号',
    item_type VARCHAR(50) NOT NULL COMMENT '问题类型',
    description TEXT NOT NULL COMMENT '问题描述',
    responsible_party VARCHAR(50) NOT NULL COMMENT '责任方',
    responsible_person_id INT COMMENT '责任人ID',
    due_date DATETIME COMMENT '截止日期',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '当前状态',
    close_evidence TEXT COMMENT '关闭证据(附件/链接/记录)',
    blocks_quotation BOOLEAN DEFAULT FALSE COMMENT '是否阻塞报价',
    closed_at DATETIME COMMENT '关闭时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_open_item_source (source_type, source_id),
    INDEX idx_open_item_status (status),
    INDEX idx_open_item_type (item_type),
    INDEX idx_open_item_blocks (blocks_quotation),
    INDEX idx_open_item_due_date (due_date),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='未决事项表';

-- 7) AI Clarifications
CREATE TABLE IF NOT EXISTS ai_clarifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL COMMENT '来源类型：LEAD/OPPORTUNITY',
    source_id INT NOT NULL COMMENT '来源ID',
    round INT NOT NULL COMMENT '澄清轮次',
    questions TEXT NOT NULL COMMENT 'AI生成的问题(JSON Array)',
    answers TEXT COMMENT '用户回答(JSON Array)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_clarification_source (source_type, source_id),
    INDEX idx_ai_clarification_round (round)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI澄清记录表';

-- 8) Extend leads table
ALTER TABLE leads 
    ADD COLUMN requirement_detail_id INT COMMENT '需求详情ID',
    ADD COLUMN assessment_id INT COMMENT '技术评估ID',
    ADD COLUMN completeness INT DEFAULT 0 COMMENT '完整度(0-100)',
    ADD COLUMN assignee_id INT COMMENT '被指派的售前工程师ID',
    ADD COLUMN assessment_status VARCHAR(20) COMMENT '技术评估状态',
    ADD INDEX idx_lead_assessment (assessment_id),
    ADD INDEX idx_lead_assignee (assignee_id),
    ADD FOREIGN KEY (requirement_detail_id) REFERENCES lead_requirement_details(id),
    ADD FOREIGN KEY (assessment_id) REFERENCES technical_assessments(id),
    ADD FOREIGN KEY (assignee_id) REFERENCES users(id);

-- 9) Extend opportunities table
ALTER TABLE opportunities 
    ADD COLUMN assessment_id INT COMMENT '技术评估ID',
    ADD COLUMN requirement_maturity INT COMMENT '需求成熟度(1-5)',
    ADD COLUMN assessment_status VARCHAR(20) COMMENT '技术评估状态',
    ADD INDEX idx_opportunity_assessment (assessment_id),
    ADD FOREIGN KEY (assessment_id) REFERENCES technical_assessments(id);






