-- ================================================================
-- 资源冲突智能调度系统数据库表
-- 创建时间: 2026-02-15
-- 作用: 资源冲突检测 + AI智能调度推荐
-- ================================================================

-- 1. 资源冲突检测表（增强版）
-- 基于现有 resource_conflicts 表，新增AI检测字段
CREATE TABLE IF NOT EXISTS resource_conflict_detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基础冲突信息
    conflict_type VARCHAR(20) NOT NULL DEFAULT 'PERSON',     -- 冲突类型: PERSON/DEVICE/WORKLOAD
    conflict_code VARCHAR(50) UNIQUE NOT NULL,               -- 冲突编码
    conflict_name VARCHAR(200) NOT NULL,                     -- 冲突名称
    
    -- 涉及资源
    resource_id INTEGER NOT NULL,                            -- 资源ID（人员ID或设备ID）
    resource_type VARCHAR(20) NOT NULL,                      -- 资源类型: PERSON/DEVICE
    resource_name VARCHAR(100),                              -- 资源名称
    department_name VARCHAR(100),                            -- 所属部门
    
    -- 冲突项目A
    project_a_id INTEGER NOT NULL REFERENCES projects(id),   -- 项目A ID
    project_a_code VARCHAR(50),                              -- 项目A编码
    project_a_name VARCHAR(200),                             -- 项目A名称
    allocation_a_id INTEGER REFERENCES pmo_resource_allocation(id), -- 分配记录A
    allocation_a_percent DECIMAL(5,2),                       -- 分配比例A (%)
    start_date_a DATE,                                       -- 开始日期A
    end_date_a DATE,                                         -- 结束日期A
    
    -- 冲突项目B
    project_b_id INTEGER NOT NULL REFERENCES projects(id),   -- 项目B ID
    project_b_code VARCHAR(50),                              -- 项目B编码
    project_b_name VARCHAR(200),                             -- 项目B名称
    allocation_b_id INTEGER REFERENCES pmo_resource_allocation(id), -- 分配记录B
    allocation_b_percent DECIMAL(5,2),                       -- 分配比例B (%)
    start_date_b DATE,                                       -- 开始日期B
    end_date_b DATE,                                         -- 结束日期B
    
    -- 冲突时间范围
    overlap_start DATE NOT NULL,                             -- 重叠开始日期
    overlap_end DATE NOT NULL,                               -- 重叠结束日期
    overlap_days INTEGER,                                    -- 重叠天数
    
    -- 冲突程度
    total_allocation DECIMAL(5,2) NOT NULL,                  -- 总分配比例 (%)
    over_allocation DECIMAL(5,2),                            -- 过度分配 (%)
    severity VARCHAR(20) DEFAULT 'MEDIUM',                   -- 严重程度: LOW/MEDIUM/HIGH/CRITICAL
    priority_score INTEGER DEFAULT 50,                       -- 优先级评分 (0-100)
    
    -- 工作负载指标
    planned_hours_a DECIMAL(10,2),                           -- 计划工时A
    planned_hours_b DECIMAL(10,2),                           -- 计划工时B
    total_planned_hours DECIMAL(10,2),                       -- 总计划工时
    weekly_capacity DECIMAL(10,2) DEFAULT 40.0,              -- 周容量（小时）
    workload_ratio DECIMAL(5,2),                             -- 工作负载比率
    
    -- AI检测信息
    detected_by VARCHAR(20) DEFAULT 'SYSTEM',                -- 检测方式: SYSTEM/AI/MANUAL
    ai_confidence DECIMAL(5,4),                              -- AI置信度 (0-1)
    ai_risk_factors TEXT,                                    -- AI识别的风险因素(JSON)
    ai_impact_analysis TEXT,                                 -- AI影响分析(JSON)
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'DETECTED',                   -- 状态: DETECTED/ANALYZING/RESOLVED/IGNORED
    is_resolved BOOLEAN DEFAULT 0,                           -- 是否已解决
    resolved_by INTEGER REFERENCES users(id),                -- 解决人
    resolved_at DATETIME,                                    -- 解决时间
    resolution_method VARCHAR(50),                           -- 解决方法
    resolution_note TEXT,                                    -- 解决说明
    
    -- AI推荐方案
    has_ai_suggestion BOOLEAN DEFAULT 0,                     -- 是否有AI推荐方案
    suggested_solution_id INTEGER,                           -- 推荐方案ID
    
    -- 通知记录
    notification_sent BOOLEAN DEFAULT 0,                     -- 是否已通知
    notification_sent_at DATETIME,                           -- 通知时间
    notified_users TEXT,                                     -- 已通知用户(JSON)
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    remark TEXT                                              -- 备注
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_conflict_detect_resource ON resource_conflict_detection(resource_id);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_type ON resource_conflict_detection(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_status ON resource_conflict_detection(status);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_severity ON resource_conflict_detection(severity);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_project_a ON resource_conflict_detection(project_a_id);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_project_b ON resource_conflict_detection(project_b_id);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_overlap ON resource_conflict_detection(overlap_start, overlap_end);
CREATE INDEX IF NOT EXISTS idx_conflict_detect_resolved ON resource_conflict_detection(is_resolved);


-- 2. AI调度方案推荐表
CREATE TABLE IF NOT EXISTS resource_scheduling_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联冲突
    conflict_id INTEGER NOT NULL REFERENCES resource_conflict_detection(id), -- 冲突ID
    suggestion_code VARCHAR(50) UNIQUE NOT NULL,             -- 方案编码
    suggestion_name VARCHAR(200) NOT NULL,                   -- 方案名称
    
    -- 方案类型
    solution_type VARCHAR(30) NOT NULL,                      -- 方案类型: RESCHEDULE/REALLOCATE/HIRE/OVERTIME/PRIORITIZE
    solution_category VARCHAR(20) DEFAULT 'AI',              -- 方案来源: AI/MANUAL/HYBRID
    
    -- 调度策略
    strategy_name VARCHAR(100),                              -- 策略名称
    strategy_description TEXT,                               -- 策略描述
    
    -- 调整建议（JSON格式）
    adjustments TEXT NOT NULL,                               -- 调整详情(JSON)
    -- 示例: {
    --   "project_a": {"action": "DELAY", "new_start": "2026-03-01", "delay_days": 7},
    --   "project_b": {"action": "REDUCE_ALLOCATION", "new_percent": 50}
    -- }
    
    -- AI评估指标
    ai_score DECIMAL(5,2) NOT NULL,                          -- AI综合评分 (0-100)
    feasibility_score DECIMAL(5,2),                          -- 可行性评分 (0-100)
    impact_score DECIMAL(5,2),                               -- 影响评分 (0-100，越低越好)
    cost_score DECIMAL(5,2),                                 -- 成本评分 (0-100，越低越好)
    risk_score DECIMAL(5,2),                                 -- 风险评分 (0-100，越低越好)
    efficiency_score DECIMAL(5,2),                           -- 效率评分 (0-100)
    
    -- 优劣分析
    pros TEXT,                                               -- 优势分析(JSON数组)
    cons TEXT,                                               -- 劣势分析(JSON数组)
    risks TEXT,                                              -- 风险点(JSON数组)
    
    -- 影响评估
    affected_projects TEXT,                                  -- 受影响项目(JSON)
    affected_resources TEXT,                                 -- 受影响资源(JSON)
    timeline_impact_days INTEGER,                            -- 时间影响（天数）
    cost_impact DECIMAL(12,2),                               -- 成本影响（元）
    quality_impact VARCHAR(20),                              -- 质量影响: NONE/LOW/MEDIUM/HIGH
    
    -- 资源需求
    additional_resources_needed TEXT,                        -- 需要额外资源(JSON)
    skill_requirements TEXT,                                 -- 技能要求(JSON)
    
    -- 执行计划
    execution_steps TEXT,                                    -- 执行步骤(JSON数组)
    estimated_duration_days INTEGER,                         -- 预计执行天数
    prerequisites TEXT,                                      -- 前置条件(JSON)
    
    -- AI推理过程
    ai_reasoning TEXT,                                       -- AI推理过程
    ai_model VARCHAR(50) DEFAULT 'GLM-5',                    -- 使用的AI模型
    ai_version VARCHAR(20),                                  -- AI模型版本
    ai_generated_at DATETIME,                                -- AI生成时间
    ai_tokens_used INTEGER,                                  -- 消耗的Token数
    
    -- 推荐排名
    rank_order INTEGER DEFAULT 1,                            -- 推荐排序（1=最优）
    is_recommended BOOLEAN DEFAULT 0,                        -- 是否系统推荐
    recommendation_reason TEXT,                              -- 推荐理由
    
    -- 采纳情况
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态: PENDING/ACCEPTED/REJECTED/IMPLEMENTED
    reviewed_by INTEGER REFERENCES users(id),                -- 审核人
    reviewed_at DATETIME,                                    -- 审核时间
    review_comment TEXT,                                     -- 审核意见
    
    implemented_by INTEGER REFERENCES users(id),             -- 执行人
    implemented_at DATETIME,                                 -- 执行时间
    implementation_result TEXT,                              -- 执行结果
    
    -- 反馈学习
    user_rating INTEGER,                                     -- 用户评分 (1-5)
    user_feedback TEXT,                                      -- 用户反馈
    actual_effectiveness DECIMAL(5,2),                       -- 实际有效性 (0-100)
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    remark TEXT                                              -- 备注
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_suggestion_conflict ON resource_scheduling_suggestions(conflict_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_type ON resource_scheduling_suggestions(solution_type);
CREATE INDEX IF NOT EXISTS idx_suggestion_status ON resource_scheduling_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_suggestion_score ON resource_scheduling_suggestions(ai_score DESC);
CREATE INDEX IF NOT EXISTS idx_suggestion_rank ON resource_scheduling_suggestions(rank_order);
CREATE INDEX IF NOT EXISTS idx_suggestion_recommended ON resource_scheduling_suggestions(is_recommended);


-- 3. 资源需求预测表
CREATE TABLE IF NOT EXISTS resource_demand_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 预测基本信息
    forecast_code VARCHAR(50) UNIQUE NOT NULL,               -- 预测编码
    forecast_name VARCHAR(200) NOT NULL,                     -- 预测名称
    forecast_period VARCHAR(20) NOT NULL,                    -- 预测周期: 1MONTH/3MONTH/6MONTH/1YEAR
    
    -- 预测时间范围
    forecast_start_date DATE NOT NULL,                       -- 预测开始日期
    forecast_end_date DATE NOT NULL,                         -- 预测结束日期
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 生成时间
    
    -- 资源类型
    resource_type VARCHAR(20) NOT NULL,                      -- 资源类型: PERSON/DEVICE/SKILL
    
    -- 按技能分类（人员）
    skill_category VARCHAR(100),                             -- 技能类别
    skill_level VARCHAR(20),                                 -- 技能等级: JUNIOR/INTERMEDIATE/SENIOR/EXPERT
    
    -- 需求量预测
    current_supply INTEGER,                                  -- 当前供给量
    predicted_demand INTEGER,                                -- 预测需求量
    demand_gap INTEGER,                                      -- 需求缺口（负数=过剩）
    gap_severity VARCHAR(20),                                -- 缺口严重程度: SURPLUS/BALANCED/SHORTAGE/CRITICAL
    
    -- 工时预测
    predicted_total_hours DECIMAL(12,2),                     -- 预测总工时
    predicted_peak_hours DECIMAL(12,2),                      -- 预测峰值工时
    predicted_avg_weekly_hours DECIMAL(8,2),                 -- 预测周均工时
    
    -- 利用率预测
    predicted_utilization DECIMAL(5,2),                      -- 预测利用率 (%)
    peak_utilization DECIMAL(5,2),                           -- 峰值利用率 (%)
    low_utilization_periods TEXT,                            -- 低利用期(JSON)
    
    -- 项目驱动因素
    driving_projects TEXT,                                   -- 驱动项目(JSON)
    project_count INTEGER,                                   -- 项目数量
    
    -- AI分析
    ai_model VARCHAR(50) DEFAULT 'GLM-5',                    -- AI模型
    ai_confidence DECIMAL(5,4),                              -- 预测置信度
    prediction_factors TEXT,                                 -- 预测因素(JSON)
    historical_trend TEXT,                                   -- 历史趋势分析(JSON)
    seasonality_pattern TEXT,                                -- 季节性模式(JSON)
    
    -- 建议措施
    recommendations TEXT,                                    -- 推荐措施(JSON数组)
    hiring_suggestion TEXT,                                  -- 招聘建议(JSON)
    training_suggestion TEXT,                                -- 培训建议(JSON)
    outsourcing_suggestion TEXT,                             -- 外包建议(JSON)
    
    -- 成本估算
    estimated_cost DECIMAL(12,2),                            -- 预估成本
    cost_breakdown TEXT,                                     -- 成本明细(JSON)
    
    -- 风险评估
    risk_level VARCHAR(20) DEFAULT 'LOW',                    -- 风险等级
    risk_factors TEXT,                                       -- 风险因素(JSON)
    mitigation_plan TEXT,                                    -- 风险缓解计划(JSON)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',                     -- 状态: ACTIVE/ARCHIVED
    accuracy_rating DECIMAL(5,2),                            -- 准确率（事后评估）
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    remark TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_forecast_period ON resource_demand_forecast(forecast_start_date, forecast_end_date);
CREATE INDEX IF NOT EXISTS idx_forecast_type ON resource_demand_forecast(resource_type);
CREATE INDEX IF NOT EXISTS idx_forecast_skill ON resource_demand_forecast(skill_category);
CREATE INDEX IF NOT EXISTS idx_forecast_gap ON resource_demand_forecast(demand_gap);
CREATE INDEX IF NOT EXISTS idx_forecast_status ON resource_demand_forecast(status);


-- 4. 资源利用率分析表
CREATE TABLE IF NOT EXISTS resource_utilization_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 分析基本信息
    analysis_code VARCHAR(50) UNIQUE NOT NULL,               -- 分析编码
    analysis_name VARCHAR(200) NOT NULL,                     -- 分析名称
    analysis_period VARCHAR(20) NOT NULL,                    -- 分析周期: DAILY/WEEKLY/MONTHLY/QUARTERLY
    
    -- 分析时间范围
    period_start_date DATE NOT NULL,                         -- 期间开始
    period_end_date DATE NOT NULL,                           -- 期间结束
    period_days INTEGER,                                     -- 期间天数
    
    -- 资源信息
    resource_id INTEGER NOT NULL,                            -- 资源ID
    resource_type VARCHAR(20) NOT NULL,                      -- 资源类型: PERSON/DEVICE
    resource_name VARCHAR(100),                              -- 资源名称
    department_name VARCHAR(100),                            -- 部门
    skill_category VARCHAR(100),                             -- 技能类别
    
    -- 工时统计
    total_available_hours DECIMAL(10,2),                     -- 总可用工时
    total_allocated_hours DECIMAL(10,2),                     -- 总分配工时
    total_actual_hours DECIMAL(10,2),                        -- 总实际工时
    total_idle_hours DECIMAL(10,2),                          -- 总闲置工时
    total_overtime_hours DECIMAL(10,2),                      -- 总加班工时
    
    -- 利用率指标
    utilization_rate DECIMAL(5,2),                           -- 利用率 (%)
    allocation_rate DECIMAL(5,2),                            -- 分配率 (%)
    efficiency_rate DECIMAL(5,2),                            -- 效率率 (实际/分配) (%)
    idle_rate DECIMAL(5,2),                                  -- 闲置率 (%)
    overtime_rate DECIMAL(5,2),                              -- 加班率 (%)
    
    -- 状态分类
    utilization_status VARCHAR(20),                          -- 利用状态: UNDERUTILIZED/NORMAL/OVERUTILIZED/CRITICAL
    is_idle_resource BOOLEAN DEFAULT 0,                      -- 是否闲置资源
    is_overloaded BOOLEAN DEFAULT 0,                         -- 是否超负荷
    
    -- 项目分布
    project_count INTEGER,                                   -- 项目数量
    active_projects TEXT,                                    -- 活跃项目(JSON)
    project_distribution TEXT,                               -- 项目工时分布(JSON)
    
    -- 时间分布
    daily_utilization TEXT,                                  -- 每日利用率(JSON)
    weekly_utilization TEXT,                                 -- 每周利用率(JSON)
    peak_utilization_date DATE,                              -- 峰值日期
    low_utilization_periods TEXT,                            -- 低谷时段(JSON)
    
    -- AI分析洞察
    ai_insights TEXT,                                        -- AI洞察(JSON)
    optimization_suggestions TEXT,                           -- 优化建议(JSON)
    reallocation_opportunities TEXT,                         -- 再分配机会(JSON)
    
    -- 成本分析
    labor_cost DECIMAL(12,2),                                -- 人工成本
    idle_cost DECIMAL(12,2),                                 -- 闲置成本
    overtime_cost DECIMAL(12,2),                             -- 加班成本
    total_cost DECIMAL(12,2),                                -- 总成本
    cost_efficiency DECIMAL(5,2),                            -- 成本效率评分
    
    -- 趋势对比
    previous_period_utilization DECIMAL(5,2),                -- 上期利用率
    utilization_change DECIMAL(5,2),                         -- 利用率变化
    trend VARCHAR(20),                                       -- 趋势: IMPROVING/STABLE/DECLINING
    
    -- 预警
    has_alert BOOLEAN DEFAULT 0,                             -- 是否有预警
    alert_type VARCHAR(30),                                  -- 预警类型
    alert_message TEXT,                                      -- 预警信息
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    remark TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_utilization_resource ON resource_utilization_analysis(resource_id);
CREATE INDEX IF NOT EXISTS idx_utilization_period ON resource_utilization_analysis(period_start_date, period_end_date);
CREATE INDEX IF NOT EXISTS idx_utilization_status ON resource_utilization_analysis(utilization_status);
CREATE INDEX IF NOT EXISTS idx_utilization_rate ON resource_utilization_analysis(utilization_rate);
CREATE INDEX IF NOT EXISTS idx_utilization_idle ON resource_utilization_analysis(is_idle_resource);
CREATE INDEX IF NOT EXISTS idx_utilization_overloaded ON resource_utilization_analysis(is_overloaded);


-- 5. 调度操作日志表
CREATE TABLE IF NOT EXISTS resource_scheduling_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联对象
    conflict_id INTEGER REFERENCES resource_conflict_detection(id), -- 冲突ID
    suggestion_id INTEGER REFERENCES resource_scheduling_suggestions(id), -- 方案ID
    
    -- 操作信息
    action_type VARCHAR(30) NOT NULL,                        -- 操作类型: DETECT/ANALYZE/SUGGEST/REVIEW/IMPLEMENT/RESOLVE
    action_desc TEXT,                                        -- 操作描述
    
    -- 操作人
    operator_id INTEGER REFERENCES users(id),                -- 操作人
    operator_name VARCHAR(100),                              -- 操作人姓名
    operator_role VARCHAR(50),                               -- 操作人角色
    
    -- 操作结果
    result VARCHAR(20),                                      -- 结果: SUCCESS/FAILED/PARTIAL
    result_data TEXT,                                        -- 结果数据(JSON)
    error_message TEXT,                                      -- 错误信息
    
    -- 性能指标
    execution_time_ms INTEGER,                               -- 执行时间(毫秒)
    ai_tokens_used INTEGER,                                  -- AI Token消耗
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),                                  -- IP地址
    user_agent TEXT                                          -- User Agent
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_log_conflict ON resource_scheduling_logs(conflict_id);
CREATE INDEX IF NOT EXISTS idx_log_suggestion ON resource_scheduling_logs(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_log_action ON resource_scheduling_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_log_operator ON resource_scheduling_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_log_time ON resource_scheduling_logs(created_at);
