# -*- coding: utf-8 -*-
"""
变更影响智能分析系统 ORM 模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ChangeImpactAnalysis(Base, TimestampMixin):
    """变更影响分析表"""
    __tablename__ = "change_impact_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    change_request_id = Column(Integer, ForeignKey("change_requests.id"), nullable=False, comment="变更请求ID")
    
    # 分析元数据
    analysis_version = Column(String(20), default="V1.0", comment="分析版本")
    analysis_status = Column(String(20), default="PENDING", comment="状态: PENDING/ANALYZING/COMPLETED/FAILED")
    analysis_started_at = Column(DateTime, comment="分析开始时间")
    analysis_completed_at = Column(DateTime, comment="分析完成时间")
    analysis_duration_ms = Column(Integer, comment="分析耗时（毫秒）")
    
    # AI模型信息
    ai_model = Column(String(50), default="GLM-5", comment="使用的AI模型")
    ai_confidence_score = Column(Numeric(5, 2), comment="AI置信度分数 (0-100)")
    
    # === 进度影响分析 ===
    schedule_impact_level = Column(String(20), comment="进度影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL")
    schedule_delay_days = Column(Integer, default=0, comment="预计延期天数")
    schedule_affected_tasks_count = Column(Integer, default=0, comment="受影响任务数量")
    schedule_critical_path_affected = Column(Boolean, default=False, comment="是否影响关键路径")
    schedule_milestone_affected = Column(Boolean, default=False, comment="是否影响里程碑")
    schedule_impact_description = Column(Text, comment="进度影响描述")
    schedule_affected_tasks = Column(JSON, comment="受影响任务列表")
    schedule_affected_milestones = Column(JSON, comment="受影响里程碑")
    
    # === 成本影响分析 ===
    cost_impact_level = Column(String(20), comment="成本影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL")
    cost_impact_amount = Column(Numeric(15, 2), default=Decimal("0"), comment="成本影响金额")
    cost_impact_percentage = Column(Numeric(5, 2), comment="成本影响百分比")
    cost_breakdown = Column(JSON, comment="成本细分")
    cost_impact_description = Column(Text, comment="成本影响描述")
    cost_budget_exceeded = Column(Boolean, default=False, comment="是否超预算")
    cost_contingency_required = Column(Numeric(15, 2), comment="需要的应急预算")
    
    # === 质量影响分析 ===
    quality_impact_level = Column(String(20), comment="质量影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL")
    quality_risk_areas = Column(JSON, comment="质量风险领域")
    quality_testing_impact = Column(Text, comment="测试影响描述")
    quality_acceptance_impact = Column(Text, comment="验收影响描述")
    quality_mitigation_required = Column(Boolean, default=False, comment="是否需要缓解措施")
    quality_impact_description = Column(Text, comment="质量影响描述")
    
    # === 资源影响分析 ===
    resource_impact_level = Column(String(20), comment="资源影响级别: NONE/LOW/MEDIUM/HIGH/CRITICAL")
    resource_additional_required = Column(JSON, comment="需要增加的资源")
    resource_reallocation_needed = Column(Boolean, default=False, comment="是否需要重新分配资源")
    resource_conflict_detected = Column(Boolean, default=False, comment="是否检测到资源冲突")
    resource_impact_description = Column(Text, comment="资源影响描述")
    resource_affected_allocations = Column(JSON, comment="受影响的资源分配")
    
    # === 连锁反应识别 ===
    chain_reaction_detected = Column(Boolean, default=False, comment="是否检测到连锁反应")
    chain_reaction_depth = Column(Integer, default=0, comment="连锁反应深度（层级）")
    chain_reaction_affected_projects = Column(JSON, comment="受影响的其他项目")
    dependency_tree = Column(JSON, comment="依赖关系树")
    critical_dependencies = Column(JSON, comment="关键依赖关系")
    
    # === 综合风险评估 ===
    overall_risk_score = Column(Numeric(5, 2), comment="综合风险评分 (0-100)")
    overall_risk_level = Column(String(20), comment="综合风险级别: LOW/MEDIUM/HIGH/CRITICAL")
    risk_factors = Column(JSON, comment="风险因素")
    recommended_action = Column(String(50), comment="推荐行动: APPROVE/REJECT/MODIFY/ESCALATE")
    
    # 分析详情
    analysis_summary = Column(Text, comment="分析摘要")
    analysis_details = Column(JSON, comment="完整分析详情")
    ai_raw_response = Column(JSON, comment="AI原始响应")
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), comment="分析发起人ID")
    
    # 关系
    change_request = relationship("ChangeRequest", back_populates="impact_analyses", lazy="joined")
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    response_suggestions = relationship(
        "ChangeResponseSuggestion",
        back_populates="impact_analysis",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        Index("idx_impact_change", "change_request_id"),
        Index("idx_impact_status", "analysis_status"),
        Index("idx_impact_risk_level", "overall_risk_level"),
        Index("idx_impact_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<ChangeImpactAnalysis id={self.id} change_request_id={self.change_request_id}>"


class ChangeResponseSuggestion(Base, TimestampMixin):
    """变更应对方案建议表"""
    __tablename__ = "change_response_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    change_request_id = Column(Integer, ForeignKey("change_requests.id"), nullable=False, comment="变更请求ID")
    impact_analysis_id = Column(
        Integer,
        ForeignKey("change_impact_analysis.id", ondelete="SET NULL"),
        comment="关联的影响分析ID"
    )
    
    # 方案基本信息
    suggestion_code = Column(String(50), comment="方案编号")
    suggestion_title = Column(String(200), nullable=False, comment="方案标题")
    suggestion_type = Column(String(50), comment="方案类型: APPROVE/REJECT/MODIFY/MITIGATE/POSTPONE")
    suggestion_priority = Column(Integer, default=0, comment="优先级 (1-10, 10最高)")
    
    # 方案描述
    summary = Column(Text, comment="方案摘要")
    detailed_description = Column(Text, comment="详细描述")
    action_steps = Column(JSON, comment="执行步骤")
    
    # === 方案影响评估 ===
    estimated_cost = Column(Numeric(15, 2), comment="预估成本")
    estimated_duration_days = Column(Integer, comment="预估工期（天）")
    resource_requirements = Column(JSON, comment="资源需求")
    dependencies = Column(JSON, comment="依赖条件")
    
    # === 风险与机会 ===
    risks = Column(JSON, comment="风险")
    opportunities = Column(JSON, comment="机会")
    risk_mitigation_plan = Column(Text, comment="风险缓解计划")
    
    # === 方案可行性 ===
    feasibility_score = Column(Numeric(5, 2), comment="可行性评分 (0-100)")
    technical_feasibility = Column(String(20), comment="技术可行性: LOW/MEDIUM/HIGH")
    cost_feasibility = Column(String(20), comment="成本可行性: LOW/MEDIUM/HIGH")
    schedule_feasibility = Column(String(20), comment="进度可行性: LOW/MEDIUM/HIGH")
    feasibility_analysis = Column(Text, comment="可行性分析")
    
    # === 预期效果 ===
    expected_outcomes = Column(JSON, comment="预期结果")
    success_criteria = Column(JSON, comment="成功标准")
    kpi_impacts = Column(JSON, comment="KPI影响")
    
    # === AI推荐 ===
    ai_recommendation_score = Column(Numeric(5, 2), comment="AI推荐分数 (0-100)")
    ai_confidence_level = Column(String(20), comment="AI置信度: LOW/MEDIUM/HIGH")
    ai_reasoning = Column(Text, comment="AI推理过程")
    alternative_suggestions = Column(JSON, comment="替代方案")
    
    # 方案状态
    status = Column(String(20), default="PROPOSED", comment="状态: PROPOSED/REVIEWED/SELECTED/REJECTED/IMPLEMENTED")
    selected_at = Column(DateTime, comment="选择时间")
    selected_by = Column(Integer, ForeignKey("users.id"), comment="选择人ID")
    selection_reason = Column(Text, comment="选择理由")
    
    # 实施跟踪
    implementation_status = Column(String(20), comment="实施状态: NOT_STARTED/IN_PROGRESS/COMPLETED/CANCELLED")
    implementation_start_date = Column(DateTime, comment="实施开始日期")
    implementation_end_date = Column(DateTime, comment="实施结束日期")
    implementation_notes = Column(Text, comment="实施备注")
    actual_cost = Column(Numeric(15, 2), comment="实际成本")
    actual_duration_days = Column(Integer, comment="实际工期")
    
    # 效果评估
    effectiveness_score = Column(Numeric(5, 2), comment="有效性评分 (0-100)")
    lessons_learned = Column(Text, comment="经验教训")
    evaluation_notes = Column(Text, comment="评估备注")
    evaluated_at = Column(DateTime, comment="评估时间")
    evaluated_by = Column(Integer, ForeignKey("users.id"), comment="评估人ID")
    
    # 附件
    attachments = Column(JSON, comment="附件列表")
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    change_request = relationship("ChangeRequest", back_populates="response_suggestions", lazy="joined")
    impact_analysis = relationship("ChangeImpactAnalysis", back_populates="response_suggestions", lazy="joined")
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    selector = relationship("User", foreign_keys=[selected_by], lazy="select")
    evaluator = relationship("User", foreign_keys=[evaluated_by], lazy="select")

    __table_args__ = (
        Index("idx_suggestion_change", "change_request_id"),
        Index("idx_suggestion_impact", "impact_analysis_id"),
        Index("idx_suggestion_status", "status"),
        Index("idx_suggestion_type", "suggestion_type"),
        Index("idx_suggestion_priority", "suggestion_priority"),
        Index("idx_suggestion_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<ChangeResponseSuggestion id={self.id} title={self.suggestion_title}>"
