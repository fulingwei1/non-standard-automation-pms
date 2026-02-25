# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - 数据模型
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ResourceConflictDetection(Base, TimestampMixin):
    """资源冲突检测表"""

    __tablename__ = "resource_conflict_detection"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基础冲突信息
    conflict_type = Column(String(20), nullable=False, default="PERSON", comment="冲突类型: PERSON/DEVICE/WORKLOAD")
    conflict_code = Column(String(50), unique=True, nullable=False, comment="冲突编码")
    conflict_name = Column(String(200), nullable=False, comment="冲突名称")
    
    # 涉及资源
    resource_id = Column(Integer, nullable=False, comment="资源ID")
    resource_type = Column(String(20), nullable=False, comment="资源类型: PERSON/DEVICE")
    resource_name = Column(String(100), comment="资源名称")
    department_name = Column(String(100), comment="所属部门")
    
    # 冲突项目A
    project_a_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目A ID")
    project_a_code = Column(String(50), comment="项目A编码")
    project_a_name = Column(String(200), comment="项目A名称")
    allocation_a_id = Column(Integer, ForeignKey("pmo_resource_allocation.id"), comment="分配记录A")
    allocation_a_percent = Column(DECIMAL(5, 2), comment="分配比例A (%)")
    start_date_a = Column(Date, comment="开始日期A")
    end_date_a = Column(Date, comment="结束日期A")
    
    # 冲突项目B
    project_b_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目B ID")
    project_b_code = Column(String(50), comment="项目B编码")
    project_b_name = Column(String(200), comment="项目B名称")
    allocation_b_id = Column(Integer, ForeignKey("pmo_resource_allocation.id"), comment="分配记录B")
    allocation_b_percent = Column(DECIMAL(5, 2), comment="分配比例B (%)")
    start_date_b = Column(Date, comment="开始日期B")
    end_date_b = Column(Date, comment="结束日期B")
    
    # 冲突时间范围
    overlap_start = Column(Date, nullable=False, comment="重叠开始日期")
    overlap_end = Column(Date, nullable=False, comment="重叠结束日期")
    overlap_days = Column(Integer, comment="重叠天数")
    
    # 冲突程度
    total_allocation = Column(DECIMAL(5, 2), nullable=False, comment="总分配比例 (%)")
    over_allocation = Column(DECIMAL(5, 2), comment="过度分配 (%)")
    severity = Column(String(20), default="MEDIUM", comment="严重程度: LOW/MEDIUM/HIGH/CRITICAL")
    priority_score = Column(Integer, default=50, comment="优先级评分 (0-100)")
    
    # 工作负载指标
    planned_hours_a = Column(DECIMAL(10, 2), comment="计划工时A")
    planned_hours_b = Column(DECIMAL(10, 2), comment="计划工时B")
    total_planned_hours = Column(DECIMAL(10, 2), comment="总计划工时")
    weekly_capacity = Column(DECIMAL(10, 2), default=40.0, comment="周容量（小时）")
    workload_ratio = Column(DECIMAL(5, 2), comment="工作负载比率")
    
    # AI检测信息
    detected_by = Column(String(20), default="SYSTEM", comment="检测方式: SYSTEM/AI/MANUAL")
    ai_confidence = Column(DECIMAL(5, 4), comment="AI置信度 (0-1)")
    ai_risk_factors = Column(Text, comment="AI识别的风险因素(JSON)")
    ai_impact_analysis = Column(Text, comment="AI影响分析(JSON)")
    
    # 处理状态
    status = Column(String(20), default="DETECTED", comment="状态: DETECTED/ANALYZING/RESOLVED/IGNORED")
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_by = Column(Integer, ForeignKey("users.id"), comment="解决人")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution_method = Column(String(50), comment="解决方法")
    resolution_note = Column(Text, comment="解决说明")
    
    # AI推荐方案
    has_ai_suggestion = Column(Boolean, default=False, comment="是否有AI推荐方案")
    suggested_solution_id = Column(Integer, comment="推荐方案ID")
    
    # 通知记录
    notification_sent = Column(Boolean, default=False, comment="是否已通知")
    notification_sent_at = Column(DateTime, comment="通知时间")
    notified_users = Column(Text, comment="已通知用户(JSON)")
    
    # 元数据
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    remark = Column(Text, comment="备注")
    
    # 关系
    project_a = relationship("Project", foreign_keys=[project_a_id], backref="conflicts_as_a")
    project_b = relationship("Project", foreign_keys=[project_b_id], backref="conflicts_as_b")
    resolver = relationship("User", foreign_keys=[resolved_by], backref="resolved_conflicts")
    creator = relationship("User", foreign_keys=[created_by], backref="created_conflicts")
    suggestions = relationship("ResourceSchedulingSuggestion", back_populates="conflict", cascade="all, delete-orphan")
    logs = relationship("ResourceSchedulingLog", back_populates="conflict", cascade="all, delete-orphan")


class ResourceSchedulingSuggestion(Base, TimestampMixin):
    """AI调度方案推荐表"""

    __tablename__ = "resource_scheduling_suggestions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联冲突
    conflict_id = Column(Integer, ForeignKey("resource_conflict_detection.id"), nullable=False, comment="冲突ID")
    suggestion_code = Column(String(50), unique=True, nullable=False, comment="方案编码")
    suggestion_name = Column(String(200), nullable=False, comment="方案名称")
    
    # 方案类型
    solution_type = Column(String(30), nullable=False, comment="方案类型: RESCHEDULE/REALLOCATE/HIRE/OVERTIME/PRIORITIZE")
    solution_category = Column(String(20), default="AI", comment="方案来源: AI/MANUAL/HYBRID")
    
    # 调度策略
    strategy_name = Column(String(100), comment="策略名称")
    strategy_description = Column(Text, comment="策略描述")
    
    # 调整建议（JSON格式）
    adjustments = Column(Text, nullable=False, comment="调整详情(JSON)")
    
    # AI评估指标
    ai_score = Column(DECIMAL(5, 2), nullable=False, comment="AI综合评分 (0-100)")
    feasibility_score = Column(DECIMAL(5, 2), comment="可行性评分 (0-100)")
    impact_score = Column(DECIMAL(5, 2), comment="影响评分 (0-100，越低越好)")
    cost_score = Column(DECIMAL(5, 2), comment="成本评分 (0-100，越低越好)")
    risk_score = Column(DECIMAL(5, 2), comment="风险评分 (0-100，越低越好)")
    efficiency_score = Column(DECIMAL(5, 2), comment="效率评分 (0-100)")
    
    # 优劣分析
    pros = Column(Text, comment="优势分析(JSON数组)")
    cons = Column(Text, comment="劣势分析(JSON数组)")
    risks = Column(Text, comment="风险点(JSON数组)")
    
    # 影响评估
    affected_projects = Column(Text, comment="受影响项目(JSON)")
    affected_resources = Column(Text, comment="受影响资源(JSON)")
    timeline_impact_days = Column(Integer, comment="时间影响（天数）")
    cost_impact = Column(DECIMAL(12, 2), comment="成本影响（元）")
    quality_impact = Column(String(20), comment="质量影响: NONE/LOW/MEDIUM/HIGH")
    
    # 资源需求
    additional_resources_needed = Column(Text, comment="需要额外资源(JSON)")
    skill_requirements = Column(Text, comment="技能要求(JSON)")
    
    # 执行计划
    execution_steps = Column(Text, comment="执行步骤(JSON数组)")
    estimated_duration_days = Column(Integer, comment="预计执行天数")
    prerequisites = Column(Text, comment="前置条件(JSON)")
    
    # AI推理过程
    ai_reasoning = Column(Text, comment="AI推理过程")
    ai_model = Column(String(50), default="GLM-5", comment="使用的AI模型")
    ai_version = Column(String(20), comment="AI模型版本")
    ai_generated_at = Column(DateTime, comment="AI生成时间")
    ai_tokens_used = Column(Integer, comment="消耗的Token数")
    
    # 推荐排名
    rank_order = Column(Integer, default=1, comment="推荐排序（1=最优）")
    is_recommended = Column(Boolean, default=False, comment="是否系统推荐")
    recommendation_reason = Column(Text, comment="推荐理由")
    
    # 采纳情况
    status = Column(String(20), default="PENDING", comment="状态: PENDING/ACCEPTED/REJECTED/IMPLEMENTED")
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人")
    reviewed_at = Column(DateTime, comment="审核时间")
    review_comment = Column(Text, comment="审核意见")
    
    implemented_by = Column(Integer, ForeignKey("users.id"), comment="执行人")
    implemented_at = Column(DateTime, comment="执行时间")
    implementation_result = Column(Text, comment="执行结果")
    
    # 反馈学习
    user_rating = Column(Integer, comment="用户评分 (1-5)")
    user_feedback = Column(Text, comment="用户反馈")
    actual_effectiveness = Column(DECIMAL(5, 2), comment="实际有效性 (0-100)")
    
    # 元数据
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    remark = Column(Text, comment="备注")
    
    # 关系
    conflict = relationship("ResourceConflictDetection", back_populates="suggestions")
    reviewer = relationship("User", foreign_keys=[reviewed_by], backref="reviewed_suggestions")
    implementer = relationship("User", foreign_keys=[implemented_by], backref="implemented_suggestions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_suggestions")
    logs = relationship("ResourceSchedulingLog", back_populates="suggestion", cascade="all, delete-orphan")


class ResourceDemandForecast(Base, TimestampMixin):
    """资源需求预测表"""

    __tablename__ = "resource_demand_forecast"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 预测基本信息
    forecast_code = Column(String(50), unique=True, nullable=False, comment="预测编码")
    forecast_name = Column(String(200), nullable=False, comment="预测名称")
    forecast_period = Column(String(20), nullable=False, comment="预测周期: 1MONTH/3MONTH/6MONTH/1YEAR")
    
    # 预测时间范围
    forecast_start_date = Column(Date, nullable=False, comment="预测开始日期")
    forecast_end_date = Column(Date, nullable=False, comment="预测结束日期")
    generated_at = Column(DateTime, default=datetime.now, comment="生成时间")
    
    # 资源类型
    resource_type = Column(String(20), nullable=False, comment="资源类型: PERSON/DEVICE/SKILL")
    
    # 按技能分类（人员）
    skill_category = Column(String(100), comment="技能类别")
    skill_level = Column(String(20), comment="技能等级: JUNIOR/INTERMEDIATE/SENIOR/EXPERT")
    
    # 需求量预测
    current_supply = Column(Integer, comment="当前供给量")
    predicted_demand = Column(Integer, comment="预测需求量")
    demand_gap = Column(Integer, comment="需求缺口（负数=过剩）")
    gap_severity = Column(String(20), comment="缺口严重程度: SURPLUS/BALANCED/SHORTAGE/CRITICAL")
    
    # 工时预测
    predicted_total_hours = Column(DECIMAL(12, 2), comment="预测总工时")
    predicted_peak_hours = Column(DECIMAL(12, 2), comment="预测峰值工时")
    predicted_avg_weekly_hours = Column(DECIMAL(8, 2), comment="预测周均工时")
    
    # 利用率预测
    predicted_utilization = Column(DECIMAL(5, 2), comment="预测利用率 (%)")
    peak_utilization = Column(DECIMAL(5, 2), comment="峰值利用率 (%)")
    low_utilization_periods = Column(Text, comment="低利用期(JSON)")
    
    # 项目驱动因素
    driving_projects = Column(Text, comment="驱动项目(JSON)")
    project_count = Column(Integer, comment="项目数量")
    
    # AI分析
    ai_model = Column(String(50), default="GLM-5", comment="AI模型")
    ai_confidence = Column(DECIMAL(5, 4), comment="预测置信度")
    prediction_factors = Column(Text, comment="预测因素(JSON)")
    historical_trend = Column(Text, comment="历史趋势分析(JSON)")
    seasonality_pattern = Column(Text, comment="季节性模式(JSON)")
    
    # 建议措施
    recommendations = Column(Text, comment="推荐措施(JSON数组)")
    hiring_suggestion = Column(Text, comment="招聘建议(JSON)")
    training_suggestion = Column(Text, comment="培训建议(JSON)")
    outsourcing_suggestion = Column(Text, comment="外包建议(JSON)")
    
    # 成本估算
    estimated_cost = Column(DECIMAL(12, 2), comment="预估成本")
    cost_breakdown = Column(Text, comment="成本明细(JSON)")
    
    # 风险评估
    risk_level = Column(String(20), default="LOW", comment="风险等级")
    risk_factors = Column(Text, comment="风险因素(JSON)")
    mitigation_plan = Column(Text, comment="风险缓解计划(JSON)")
    
    # 状态
    status = Column(String(20), default="ACTIVE", comment="状态: ACTIVE/ARCHIVED")
    accuracy_rating = Column(DECIMAL(5, 2), comment="准确率（事后评估）")
    
    # 元数据
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    remark = Column(Text, comment="备注")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by], backref="created_forecasts")


class ResourceUtilizationAnalysis(Base, TimestampMixin):
    """资源利用率分析表"""

    __tablename__ = "resource_utilization_analysis"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 分析基本信息
    analysis_code = Column(String(50), unique=True, nullable=False, comment="分析编码")
    analysis_name = Column(String(200), nullable=False, comment="分析名称")
    analysis_period = Column(String(20), nullable=False, comment="分析周期: DAILY/WEEKLY/MONTHLY/QUARTERLY")
    
    # 分析时间范围
    period_start_date = Column(Date, nullable=False, comment="期间开始")
    period_end_date = Column(Date, nullable=False, comment="期间结束")
    period_days = Column(Integer, comment="期间天数")
    
    # 资源信息
    resource_id = Column(Integer, nullable=False, comment="资源ID")
    resource_type = Column(String(20), nullable=False, comment="资源类型: PERSON/DEVICE")
    resource_name = Column(String(100), comment="资源名称")
    department_name = Column(String(100), comment="部门")
    skill_category = Column(String(100), comment="技能类别")
    
    # 工时统计
    total_available_hours = Column(DECIMAL(10, 2), comment="总可用工时")
    total_allocated_hours = Column(DECIMAL(10, 2), comment="总分配工时")
    total_actual_hours = Column(DECIMAL(10, 2), comment="总实际工时")
    total_idle_hours = Column(DECIMAL(10, 2), comment="总闲置工时")
    total_overtime_hours = Column(DECIMAL(10, 2), comment="总加班工时")
    
    # 利用率指标
    utilization_rate = Column(DECIMAL(5, 2), comment="利用率 (%)")
    allocation_rate = Column(DECIMAL(5, 2), comment="分配率 (%)")
    efficiency_rate = Column(DECIMAL(5, 2), comment="效率率 (实际/分配) (%)")
    idle_rate = Column(DECIMAL(5, 2), comment="闲置率 (%)")
    overtime_rate = Column(DECIMAL(5, 2), comment="加班率 (%)")
    
    # 状态分类
    utilization_status = Column(String(20), comment="利用状态: UNDERUTILIZED/NORMAL/OVERUTILIZED/CRITICAL")
    is_idle_resource = Column(Boolean, default=False, comment="是否闲置资源")
    is_overloaded = Column(Boolean, default=False, comment="是否超负荷")
    
    # 项目分布
    project_count = Column(Integer, comment="项目数量")
    active_projects = Column(Text, comment="活跃项目(JSON)")
    project_distribution = Column(Text, comment="项目工时分布(JSON)")
    
    # 时间分布
    daily_utilization = Column(Text, comment="每日利用率(JSON)")
    weekly_utilization = Column(Text, comment="每周利用率(JSON)")
    peak_utilization_date = Column(Date, comment="峰值日期")
    low_utilization_periods = Column(Text, comment="低谷时段(JSON)")
    
    # AI分析洞察
    ai_insights = Column(Text, comment="AI洞察(JSON)")
    optimization_suggestions = Column(Text, comment="优化建议(JSON)")
    reallocation_opportunities = Column(Text, comment="再分配机会(JSON)")
    
    # 成本分析
    labor_cost = Column(DECIMAL(12, 2), comment="人工成本")
    idle_cost = Column(DECIMAL(12, 2), comment="闲置成本")
    overtime_cost = Column(DECIMAL(12, 2), comment="加班成本")
    total_cost = Column(DECIMAL(12, 2), comment="总成本")
    cost_efficiency = Column(DECIMAL(5, 2), comment="成本效率评分")
    
    # 趋势对比
    previous_period_utilization = Column(DECIMAL(5, 2), comment="上期利用率")
    utilization_change = Column(DECIMAL(5, 2), comment="利用率变化")
    trend = Column(String(20), comment="趋势: IMPROVING/STABLE/DECLINING")
    
    # 预警
    has_alert = Column(Boolean, default=False, comment="是否有预警")
    alert_type = Column(String(30), comment="预警类型")
    alert_message = Column(Text, comment="预警信息")
    
    # 元数据
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    remark = Column(Text, comment="备注")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by], backref="created_utilization_analyses")


class ResourceSchedulingLog(Base):
    """调度操作日志表"""

    __tablename__ = "resource_scheduling_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联对象
    conflict_id = Column(Integer, ForeignKey("resource_conflict_detection.id"), comment="冲突ID")
    suggestion_id = Column(Integer, ForeignKey("resource_scheduling_suggestions.id"), comment="方案ID")
    
    # 操作信息
    action_type = Column(String(30), nullable=False, comment="操作类型: DETECT/ANALYZE/SUGGEST/REVIEW/IMPLEMENT/RESOLVE")
    action_desc = Column(Text, comment="操作描述")
    
    # 操作人
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人")
    operator_name = Column(String(100), comment="操作人姓名")
    operator_role = Column(String(50), comment="操作人角色")
    
    # 操作结果
    result = Column(String(20), comment="结果: SUCCESS/FAILED/PARTIAL")
    result_data = Column(Text, comment="结果数据(JSON)")
    error_message = Column(Text, comment="错误信息")
    
    # 性能指标
    execution_time_ms = Column(Integer, comment="执行时间(毫秒)")
    ai_tokens_used = Column(Integer, comment="AI Token消耗")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(Text, comment="User Agent")
    
    # 关系
    conflict = relationship("ResourceConflictDetection", back_populates="logs")
    suggestion = relationship("ResourceSchedulingSuggestion", back_populates="logs")
    operator = relationship("User", foreign_keys=[operator_id], backref="scheduling_operations")
