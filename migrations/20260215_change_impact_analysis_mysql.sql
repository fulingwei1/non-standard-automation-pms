-- ========================================
-- 变更影响智能分析系统 - MySQL
-- 创建时间: 2026-02-15
-- 描述: 变更影响分析、应对方案推荐
-- ========================================

-- ==================== 变更影响分析表 ====================

CREATE TABLE IF NOT EXISTS change_impact_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    change_request_id INT NOT NULL COMMENT '变更请求ID',
    
    -- 分析元数据
    analysis_version VARCHAR(20) DEFAULT 'V1.0' COMMENT '分析版本',
    analysis_status VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态: PENDING/ANALYZING/COMPLETED/FAILED',
    analysis_started_at DATETIME COMMENT '分析开始时间',
    analysis_completed_at DATETIME COMMENT '分析完成时间',
    analysis_duration_ms INT COMMENT '分析耗时（毫秒）',
    
    -- AI模型信息
    ai_model VARCHAR(50) DEFAULT 'GLM-5' COMMENT '使用的AI模型',
    ai_confidence_score DECIMAL(5,2) COMMENT 'AI置信度分数 (0-100)',
    
    -- === 进度影响分析 ===
    schedule_impact_level VARCHAR(20) COMMENT '进度影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL',
    schedule_delay_days INT DEFAULT 0 COMMENT '预计延期天数',
    schedule_affected_tasks_count INT DEFAULT 0 COMMENT '受影响任务数量',
    schedule_critical_path_affected BOOLEAN DEFAULT FALSE COMMENT '是否影响关键路径',
    schedule_milestone_affected BOOLEAN DEFAULT FALSE COMMENT '是否影响里程碑',
    schedule_impact_description TEXT COMMENT '进度影响描述',
    schedule_affected_tasks JSON COMMENT '受影响任务列表',
    schedule_affected_milestones JSON COMMENT '受影响里程碑',
    
    -- === 成本影响分析 ===
    cost_impact_level VARCHAR(20) COMMENT '成本影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL',
    cost_impact_amount DECIMAL(15,2) DEFAULT 0 COMMENT '成本影响金额',
    cost_impact_percentage DECIMAL(5,2) COMMENT '成本影响百分比',
    cost_breakdown JSON COMMENT '成本细分',
    cost_impact_description TEXT COMMENT '成本影响描述',
    cost_budget_exceeded BOOLEAN DEFAULT FALSE COMMENT '是否超预算',
    cost_contingency_required DECIMAL(15,2) COMMENT '需要的应急预算',
    
    -- === 质量影响分析 ===
    quality_impact_level VARCHAR(20) COMMENT '质量影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL',
    quality_risk_areas JSON COMMENT '质量风险领域',
    quality_testing_impact TEXT COMMENT '测试影响描述',
    quality_acceptance_impact TEXT COMMENT '验收影响描述',
    quality_mitigation_required BOOLEAN DEFAULT FALSE COMMENT '是否需要缓解措施',
    quality_impact_description TEXT COMMENT '质量影响描述',
    
    -- === 资源影响分析 ===
    resource_impact_level VARCHAR(20) COMMENT '资源影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL',
    resource_additional_required JSON COMMENT '需要增加的资源',
    resource_reallocation_needed BOOLEAN DEFAULT FALSE COMMENT '是否需要重新分配资源',
    resource_conflict_detected BOOLEAN DEFAULT FALSE COMMENT '是否检测到资源冲突',
    resource_impact_description TEXT COMMENT '资源影响描述',
    resource_affected_allocations JSON COMMENT '受影响的资源分配',
    
    -- === 连锁反应识别 ===
    chain_reaction_detected BOOLEAN DEFAULT FALSE COMMENT '是否检测到连锁反应',
    chain_reaction_depth INT DEFAULT 0 COMMENT '连锁反应深度（层级）',
    chain_reaction_affected_projects JSON COMMENT '受影响的其他项目',
    dependency_tree JSON COMMENT '依赖关系树',
    critical_dependencies JSON COMMENT '关键依赖关系',
    
    -- === 综合风险评估 ===
    overall_risk_score DECIMAL(5,2) COMMENT '综合风险评分 (0-100)',
    overall_risk_level VARCHAR(20) COMMENT '综合风险级别: LOW/MEDIUM/HIGH/CRITICAL',
    risk_factors JSON COMMENT '风险因素',
    recommended_action VARCHAR(50) COMMENT '推荐行动: APPROVE/REJECT/MODIFY/ESCALATE',
    
    -- 分析详情
    analysis_summary TEXT COMMENT '分析摘要',
    analysis_details JSON COMMENT '完整分析详情',
    ai_raw_response JSON COMMENT 'AI原始响应',
    
    -- 创建信息
    created_by INT COMMENT '分析发起人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_impact_change (change_request_id),
    INDEX idx_impact_status (analysis_status),
    INDEX idx_impact_risk_level (overall_risk_level),
    INDEX idx_impact_created_at (created_at),
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='变更影响分析表';

-- ==================== 变更应对方案建议表 ====================

CREATE TABLE IF NOT EXISTS change_response_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    change_request_id INT NOT NULL COMMENT '变更请求ID',
    impact_analysis_id INT COMMENT '关联的影响分析ID',
    
    -- 方案基本信息
    suggestion_code VARCHAR(50) COMMENT '方案编号',
    suggestion_title VARCHAR(200) NOT NULL COMMENT '方案标题',
    suggestion_type VARCHAR(50) COMMENT '方案类型: APPROVE/REJECT/MODIFY/MITIGATE/POSTPONE',
    suggestion_priority INT DEFAULT 0 COMMENT '优先级 (1-10, 10最高)',
    
    -- 方案描述
    summary TEXT COMMENT '方案摘要',
    detailed_description TEXT COMMENT '详细描述',
    action_steps JSON COMMENT '执行步骤',
    
    -- === 方案影响评估 ===
    estimated_cost DECIMAL(15,2) COMMENT '预估成本',
    estimated_duration_days INT COMMENT '预估工期（天）',
    resource_requirements JSON COMMENT '资源需求',
    dependencies JSON COMMENT '依赖条件',
    
    -- === 风险与机会 ===
    risks JSON COMMENT '风险',
    opportunities JSON COMMENT '机会',
    risk_mitigation_plan TEXT COMMENT '风险缓解计划',
    
    -- === 方案可行性 ===
    feasibility_score DECIMAL(5,2) COMMENT '可行性评分 (0-100)',
    technical_feasibility VARCHAR(20) COMMENT '技术可行性: LOW/MEDIUM/HIGH',
    cost_feasibility VARCHAR(20) COMMENT '成本可行性: LOW/MEDIUM/HIGH',
    schedule_feasibility VARCHAR(20) COMMENT '进度可行性: LOW/MEDIUM/HIGH',
    feasibility_analysis TEXT COMMENT '可行性分析',
    
    -- === 预期效果 ===
    expected_outcomes JSON COMMENT '预期结果',
    success_criteria JSON COMMENT '成功标准',
    kpi_impacts JSON COMMENT 'KPI影响',
    
    -- === AI推荐 ===
    ai_recommendation_score DECIMAL(5,2) COMMENT 'AI推荐分数 (0-100)',
    ai_confidence_level VARCHAR(20) COMMENT 'AI置信度: LOW/MEDIUM/HIGH',
    ai_reasoning TEXT COMMENT 'AI推理过程',
    alternative_suggestions JSON COMMENT '替代方案',
    
    -- 方案状态
    status VARCHAR(20) DEFAULT 'PROPOSED' COMMENT '状态: PROPOSED/REVIEWED/SELECTED/REJECTED/IMPLEMENTED',
    selected_at DATETIME COMMENT '选择时间',
    selected_by INT COMMENT '选择人ID',
    selection_reason TEXT COMMENT '选择理由',
    
    -- 实施跟踪
    implementation_status VARCHAR(20) COMMENT '实施状态: NOT_STARTED/IN_PROGRESS/COMPLETED/CANCELLED',
    implementation_start_date DATETIME COMMENT '实施开始日期',
    implementation_end_date DATETIME COMMENT '实施结束日期',
    implementation_notes TEXT COMMENT '实施备注',
    actual_cost DECIMAL(15,2) COMMENT '实际成本',
    actual_duration_days INT COMMENT '实际工期',
    
    -- 效果评估
    effectiveness_score DECIMAL(5,2) COMMENT '有效性评分 (0-100)',
    lessons_learned TEXT COMMENT '经验教训',
    evaluation_notes TEXT COMMENT '评估备注',
    evaluated_at DATETIME COMMENT '评估时间',
    evaluated_by INT COMMENT '评估人ID',
    
    -- 附件
    attachments JSON COMMENT '附件列表',
    
    -- 创建信息
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_suggestion_change (change_request_id),
    INDEX idx_suggestion_impact (impact_analysis_id),
    INDEX idx_suggestion_status (status),
    INDEX idx_suggestion_type (suggestion_type),
    INDEX idx_suggestion_priority (suggestion_priority),
    INDEX idx_suggestion_created_at (created_at),
    
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (impact_analysis_id) REFERENCES change_impact_analysis(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (selected_by) REFERENCES users(id),
    FOREIGN KEY (evaluated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='变更应对方案建议表';
