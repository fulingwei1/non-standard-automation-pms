-- ========================================
-- 变更影响智能分析系统 - SQLite
-- 创建时间: 2026-02-15
-- 描述: 变更影响分析、应对方案推荐
-- ========================================

-- ==================== 变更影响分析表 ====================

CREATE TABLE IF NOT EXISTS change_impact_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL, -- 变更请求ID
    
    -- 分析元数据
    analysis_version VARCHAR(20) DEFAULT 'V1.0', -- 分析版本
    analysis_status VARCHAR(20) DEFAULT 'PENDING', -- 状态: PENDING/ANALYZING/COMPLETED/FAILED
    analysis_started_at DATETIME, -- 分析开始时间
    analysis_completed_at DATETIME, -- 分析完成时间
    analysis_duration_ms INTEGER, -- 分析耗时（毫秒）
    
    -- AI模型信息
    ai_model VARCHAR(50) DEFAULT 'GLM-5', -- 使用的AI模型
    ai_confidence_score DECIMAL(5,2), -- AI置信度分数 (0-100)
    
    -- === 进度影响分析 ===
    schedule_impact_level VARCHAR(20), -- 进度影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL
    schedule_delay_days INTEGER DEFAULT 0, -- 预计延期天数
    schedule_affected_tasks_count INTEGER DEFAULT 0, -- 受影响任务数量
    schedule_critical_path_affected BOOLEAN DEFAULT 0, -- 是否影响关键路径
    schedule_milestone_affected BOOLEAN DEFAULT 0, -- 是否影响里程碑
    schedule_impact_description TEXT, -- 进度影响描述
    schedule_affected_tasks JSON, -- 受影响任务列表 [{task_id, task_name, impact_type, delay_days}]
    schedule_affected_milestones JSON, -- 受影响里程碑 [{milestone_id, name, original_date, new_date}]
    
    -- === 成本影响分析 ===
    cost_impact_level VARCHAR(20), -- 成本影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL
    cost_impact_amount DECIMAL(15,2) DEFAULT 0, -- 成本影响金额
    cost_impact_percentage DECIMAL(5,2), -- 成本影响百分比
    cost_breakdown JSON, -- 成本细分 {labor: 0, material: 0, outsourcing: 0, other: 0}
    cost_impact_description TEXT, -- 成本影响描述
    cost_budget_exceeded BOOLEAN DEFAULT 0, -- 是否超预算
    cost_contingency_required DECIMAL(15,2), -- 需要的应急预算
    
    -- === 质量影响分析 ===
    quality_impact_level VARCHAR(20), -- 质量影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL
    quality_risk_areas JSON, -- 质量风险领域 [{area, risk_level, description}]
    quality_testing_impact TEXT, -- 测试影响描述
    quality_acceptance_impact TEXT, -- 验收影响描述
    quality_mitigation_required BOOLEAN DEFAULT 0, -- 是否需要缓解措施
    quality_impact_description TEXT, -- 质量影响描述
    
    -- === 资源影响分析 ===
    resource_impact_level VARCHAR(20), -- 资源影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL
    resource_additional_required JSON, -- 需要增加的资源 [{type, quantity, skill_required}]
    resource_reallocation_needed BOOLEAN DEFAULT 0, -- 是否需要重新分配资源
    resource_conflict_detected BOOLEAN DEFAULT 0, -- 是否检测到资源冲突
    resource_impact_description TEXT, -- 资源影响描述
    resource_affected_allocations JSON, -- 受影响的资源分配
    
    -- === 连锁反应识别 ===
    chain_reaction_detected BOOLEAN DEFAULT 0, -- 是否检测到连锁反应
    chain_reaction_depth INTEGER DEFAULT 0, -- 连锁反应深度（层级）
    chain_reaction_affected_projects JSON, -- 受影响的其他项目 [{project_id, name, impact_type}]
    dependency_tree JSON, -- 依赖关系树
    critical_dependencies JSON, -- 关键依赖关系
    
    -- === 综合风险评估 ===
    overall_risk_score DECIMAL(5,2), -- 综合风险评分 (0-100)
    overall_risk_level VARCHAR(20), -- 综合风险级别: LOW/MEDIUM/HIGH/CRITICAL
    risk_factors JSON, -- 风险因素 [{factor, weight, score}]
    recommended_action VARCHAR(50), -- 推荐行动: APPROVE/REJECT/MODIFY/ESCALATE
    
    -- 分析详情
    analysis_summary TEXT, -- 分析摘要
    analysis_details JSON, -- 完整分析详情
    ai_raw_response JSON, -- AI原始响应
    
    -- 创建信息
    created_by INTEGER, -- 分析发起人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_impact_change ON change_impact_analysis(change_request_id);
CREATE INDEX idx_impact_status ON change_impact_analysis(analysis_status);
CREATE INDEX idx_impact_risk_level ON change_impact_analysis(overall_risk_level);
CREATE INDEX idx_impact_created_at ON change_impact_analysis(created_at);

-- ==================== 变更应对方案建议表 ====================

CREATE TABLE IF NOT EXISTS change_response_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL, -- 变更请求ID
    impact_analysis_id INTEGER, -- 关联的影响分析ID
    
    -- 方案基本信息
    suggestion_code VARCHAR(50), -- 方案编号
    suggestion_title VARCHAR(200) NOT NULL, -- 方案标题
    suggestion_type VARCHAR(50), -- 方案类型: APPROVE/REJECT/MODIFY/MITIGATE/POSTPONE
    suggestion_priority INTEGER DEFAULT 0, -- 优先级 (1-10, 10最高)
    
    -- 方案描述
    summary TEXT, -- 方案摘要
    detailed_description TEXT, -- 详细描述
    action_steps JSON, -- 执行步骤 [{step, description, owner, duration}]
    
    -- === 方案影响评估 ===
    estimated_cost DECIMAL(15,2), -- 预估成本
    estimated_duration_days INTEGER, -- 预估工期（天）
    resource_requirements JSON, -- 资源需求 [{type, quantity, duration}]
    dependencies JSON, -- 依赖条件
    
    -- === 风险与机会 ===
    risks JSON, -- 风险 [{risk, probability, impact, mitigation}]
    opportunities JSON, -- 机会 [{opportunity, benefit}]
    risk_mitigation_plan TEXT, -- 风险缓解计划
    
    -- === 方案可行性 ===
    feasibility_score DECIMAL(5,2), -- 可行性评分 (0-100)
    technical_feasibility VARCHAR(20), -- 技术可行性: LOW/MEDIUM/HIGH
    cost_feasibility VARCHAR(20), -- 成本可行性: LOW/MEDIUM/HIGH
    schedule_feasibility VARCHAR(20), -- 进度可行性: LOW/MEDIUM/HIGH
    feasibility_analysis TEXT, -- 可行性分析
    
    -- === 预期效果 ===
    expected_outcomes JSON, -- 预期结果 [{outcome, metric, target}]
    success_criteria JSON, -- 成功标准
    kpi_impacts JSON, -- KPI影响 [{kpi, current, expected, change}]
    
    -- === AI推荐 ===
    ai_recommendation_score DECIMAL(5,2), -- AI推荐分数 (0-100)
    ai_confidence_level VARCHAR(20), -- AI置信度: LOW/MEDIUM/HIGH
    ai_reasoning TEXT, -- AI推理过程
    alternative_suggestions JSON, -- 替代方案
    
    -- 方案状态
    status VARCHAR(20) DEFAULT 'PROPOSED', -- 状态: PROPOSED/REVIEWED/SELECTED/REJECTED/IMPLEMENTED
    selected_at DATETIME, -- 选择时间
    selected_by INTEGER, -- 选择人ID
    selection_reason TEXT, -- 选择理由
    
    -- 实施跟踪
    implementation_status VARCHAR(20), -- 实施状态: NOT_STARTED/IN_PROGRESS/COMPLETED/CANCELLED
    implementation_start_date DATETIME, -- 实施开始日期
    implementation_end_date DATETIME, -- 实施结束日期
    implementation_notes TEXT, -- 实施备注
    actual_cost DECIMAL(15,2), -- 实际成本
    actual_duration_days INTEGER, -- 实际工期
    
    -- 效果评估
    effectiveness_score DECIMAL(5,2), -- 有效性评分 (0-100)
    lessons_learned TEXT, -- 经验教训
    evaluation_notes TEXT, -- 评估备注
    evaluated_at DATETIME, -- 评估时间
    evaluated_by INTEGER, -- 评估人ID
    
    -- 附件
    attachments JSON, -- 附件列表
    
    -- 创建信息
    created_by INTEGER, -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (impact_analysis_id) REFERENCES change_impact_analysis(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (selected_by) REFERENCES users(id),
    FOREIGN KEY (evaluated_by) REFERENCES users(id)
);

CREATE INDEX idx_suggestion_change ON change_response_suggestions(change_request_id);
CREATE INDEX idx_suggestion_impact ON change_response_suggestions(impact_analysis_id);
CREATE INDEX idx_suggestion_status ON change_response_suggestions(status);
CREATE INDEX idx_suggestion_type ON change_response_suggestions(suggestion_type);
CREATE INDEX idx_suggestion_priority ON change_response_suggestions(suggestion_priority);
CREATE INDEX idx_suggestion_created_at ON change_response_suggestions(created_at);

-- ==================== 触发器：自动更新 updated_at ====================

CREATE TRIGGER update_change_impact_analysis_timestamp 
AFTER UPDATE ON change_impact_analysis
FOR EACH ROW
BEGIN
    UPDATE change_impact_analysis 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

CREATE TRIGGER update_change_response_suggestions_timestamp 
AFTER UPDATE ON change_response_suggestions
FOR EACH ROW
BEGIN
    UPDATE change_response_suggestions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;
