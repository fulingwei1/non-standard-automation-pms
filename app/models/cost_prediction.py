# -*- coding: utf-8 -*-
"""
成本预测与优化建议模型
支持AI驱动的成本超支预警和优化建议
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CostPrediction(Base, TimestampMixin):
    """
    成本预测表 - AI驱动的项目成本预测和风险评估
    
    核心功能：
    - 预测项目最终成本（EAC预测）
    - 识别成本超支风险因素
    - 计算超支概率和金额
    - 成本趋势分析
    """

    __tablename__ = "cost_prediction"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 项目关联
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余）")
    
    # 预测基准信息
    prediction_date = Column(
        Date,
        nullable=False,
        default=date.today,
        comment="预测日期"
    )
    prediction_version = Column(
        String(50),
        nullable=False,
        comment="预测版本号（如：V1.0, V2.0）"
    )
    
    # 关联的EVM数据
    evm_data_id = Column(
        Integer,
        ForeignKey("earned_value_data.id", ondelete="SET NULL"),
        comment="基准EVM数据ID"
    )
    
    # === 当前状态快照 ===
    current_pv = Column(
        Numeric(18, 4),
        comment="当前PV - 计划价值"
    )
    current_ev = Column(
        Numeric(18, 4),
        comment="当前EV - 挣得价值"
    )
    current_ac = Column(
        Numeric(18, 4),
        comment="当前AC - 实际成本"
    )
    current_bac = Column(
        Numeric(18, 4),
        comment="当前BAC - 完工预算"
    )
    current_cpi = Column(
        Numeric(10, 6),
        comment="当前CPI - 成本绩效指数"
    )
    current_spi = Column(
        Numeric(10, 6),
        comment="当前SPI - 进度绩效指数"
    )
    current_percent_complete = Column(
        Numeric(5, 2),
        comment="当前完成百分比"
    )
    
    # === AI预测结果 ===
    predicted_eac = Column(
        Numeric(18, 4),
        nullable=False,
        comment="AI预测的完工估算（Estimate at Completion）"
    )
    predicted_eac_confidence = Column(
        Numeric(5, 2),
        comment="预测置信度（0-100）"
    )
    predicted_completion_date = Column(
        Date,
        comment="预测完工日期"
    )
    
    # 预测方法
    prediction_method = Column(
        String(50),
        default="AI_GLM5",
        comment="预测方法：AI_GLM5/CPI_BASED/SPI_CPI/EXPERT/HYBRID"
    )
    
    # === 超支风险评估 ===
    overrun_probability = Column(
        Numeric(5, 2),
        comment="超支概率（0-100%）"
    )
    expected_overrun_amount = Column(
        Numeric(18, 4),
        comment="预期超支金额（VAC的负值）"
    )
    overrun_percentage = Column(
        Numeric(5, 2),
        comment="超支百分比（相对于BAC）"
    )
    
    # 风险等级
    risk_level = Column(
        String(20),
        comment="风险等级：LOW/MEDIUM/HIGH/CRITICAL"
    )
    risk_score = Column(
        Numeric(5, 2),
        comment="风险评分（0-100）"
    )
    
    # === 风险因素识别 ===
    risk_factors = Column(
        JSON,
        comment="风险因素列表（JSON数组）"
    )
    # 示例结构：
    # [
    #   {
    #     "factor": "CPI持续下降",
    #     "impact": "HIGH",
    #     "weight": 0.35,
    #     "description": "过去3个月CPI从1.05降至0.92"
    #   },
    #   {
    #     "factor": "材料成本上涨",
    #     "impact": "MEDIUM",
    #     "weight": 0.25,
    #     "description": "钢材价格上涨15%"
    #   }
    # ]
    
    # === 成本趋势分析 ===
    cost_trend = Column(
        String(20),
        comment="成本趋势：IMPROVING/STABLE/DECLINING/VOLATILE"
    )
    trend_analysis = Column(
        Text,
        comment="趋势分析详情"
    )
    
    # 历史CPI趋势
    cpi_trend_data = Column(
        JSON,
        comment="CPI历史趋势数据（最近6-12个月）"
    )
    # 示例：[{"month": "2025-08", "cpi": 1.05}, {"month": "2025-09", "cpi": 1.02}, ...]
    
    # === AI分析结果 ===
    ai_analysis_summary = Column(
        Text,
        comment="AI分析摘要"
    )
    ai_insights = Column(
        JSON,
        comment="AI洞察（结构化数据）"
    )
    # 示例结构：
    # {
    #   "key_findings": ["成本效率持续下降", "进度落后导致成本增加"],
    #   "root_causes": ["资源配置不足", "返工率高"],
    #   "critical_alerts": ["预计超支15%，需立即采取措施"]
    # }
    
    # === 预测区间 ===
    eac_lower_bound = Column(
        Numeric(18, 4),
        comment="EAC预测下限（乐观情况）"
    )
    eac_upper_bound = Column(
        Numeric(18, 4),
        comment="EAC预测上限（悲观情况）"
    )
    eac_most_likely = Column(
        Numeric(18, 4),
        comment="EAC最可能值（三点估算）"
    )
    
    # === 敏感性分析 ===
    sensitivity_analysis = Column(
        JSON,
        comment="敏感性分析结果"
    )
    # 示例：
    # {
    #   "cpi_impact": {"change_10pct": 50000, "elasticity": 0.8},
    #   "schedule_impact": {"delay_1month": 30000},
    #   "material_cost_impact": {"increase_5pct": 20000}
    # }
    
    # === 模型性能指标 ===
    model_version = Column(
        String(50),
        comment="AI模型版本"
    )
    model_accuracy = Column(
        Numeric(5, 2),
        comment="模型准确率（基于历史验证）"
    )
    training_data_count = Column(
        Integer,
        comment="训练数据数量"
    )
    
    # === 数据来源和状态 ===
    data_quality_score = Column(
        Numeric(5, 2),
        comment="数据质量评分（0-100）"
    )
    is_approved = Column(
        Boolean,
        default=False,
        comment="是否已审批"
    )
    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        comment="审批人ID"
    )
    approved_at = Column(
        DateTime,
        comment="审批时间"
    )
    
    # 备注
    notes = Column(Text, comment="备注说明")
    
    # 创建人
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        comment="创建人ID"
    )
    
    # 关系
    project = relationship("Project", back_populates="cost_predictions")
    evm_data = relationship("EarnedValueData")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    optimization_suggestions = relationship(
        "CostOptimizationSuggestion",
        back_populates="prediction",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_cost_pred_project", "project_id"),
        Index("idx_cost_pred_date", "prediction_date"),
        Index("idx_cost_pred_risk_level", "risk_level"),
        Index("idx_cost_pred_version", "project_id", "prediction_version"),
        Index("idx_cost_pred_approved", "is_approved"),
        {"comment": "成本预测表（AI驱动）"}
    )

    def __repr__(self):
        return f"<CostPrediction project={self.project_code} date={self.prediction_date} EAC={self.predicted_eac}>"


class CostOptimizationSuggestion(Base, TimestampMixin):
    """
    成本优化建议表 - AI生成的成本削减和优化建议
    
    核心功能：
    - AI生成优化措施
    - 成本削减方案
    - ROI评估
    - 实施跟踪
    """

    __tablename__ = "cost_optimization_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 关联成本预测
    prediction_id = Column(
        Integer,
        ForeignKey("cost_prediction.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的成本预测ID"
    )
    
    # 项目关联（冗余，便于查询）
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余）")
    
    # === 建议基本信息 ===
    suggestion_code = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="建议编码（如：OPT-PRJ001-2026-001）"
    )
    suggestion_title = Column(
        String(200),
        nullable=False,
        comment="建议标题"
    )
    suggestion_type = Column(
        String(50),
        comment="建议类型：RESOURCE_OPTIMIZATION/SCOPE_ADJUSTMENT/PROCESS_IMPROVEMENT/VENDOR_NEGOTIATION/SCHEDULE_OPTIMIZATION/OTHER"
    )
    
    # 优先级
    priority = Column(
        String(20),
        default="MEDIUM",
        comment="优先级：CRITICAL/HIGH/MEDIUM/LOW"
    )
    urgency = Column(
        String(20),
        comment="紧急程度：IMMEDIATE/URGENT/NORMAL/LOW"
    )
    
    # === 建议详情 ===
    description = Column(
        Text,
        nullable=False,
        comment="详细描述"
    )
    current_situation = Column(
        Text,
        comment="当前情况分析"
    )
    proposed_action = Column(
        Text,
        comment="建议采取的行动"
    )
    implementation_steps = Column(
        JSON,
        comment="实施步骤（JSON数组）"
    )
    # 示例：
    # [
    #   {"step": 1, "action": "与供应商重新谈判", "duration_days": 7, "responsible": "采购部"},
    #   {"step": 2, "action": "调整采购计划", "duration_days": 3, "responsible": "项目经理"}
    # ]
    
    # === 财务影响评估 ===
    estimated_cost_saving = Column(
        Numeric(18, 4),
        comment="预计成本节约金额"
    )
    implementation_cost = Column(
        Numeric(18, 4),
        comment="实施成本"
    )
    net_benefit = Column(
        Numeric(18, 4),
        comment="净收益（节约 - 实施成本）"
    )
    roi_percentage = Column(
        Numeric(5, 2),
        comment="投资回报率（ROI %）"
    )
    payback_period_days = Column(
        Integer,
        comment="回收期（天）"
    )
    
    # === 影响评估 ===
    impact_on_schedule = Column(
        String(20),
        comment="对进度的影响：POSITIVE/NEUTRAL/NEGATIVE"
    )
    schedule_impact_days = Column(
        Integer,
        comment="进度影响天数（正值=延迟，负值=提前）"
    )
    impact_on_quality = Column(
        String(20),
        comment="对质量的影响：POSITIVE/NEUTRAL/NEGATIVE"
    )
    impact_on_scope = Column(
        String(20),
        comment="对范围的影响：REDUCED/UNCHANGED/EXPANDED"
    )
    
    # 风险评估
    implementation_risk = Column(
        String(20),
        comment="实施风险：LOW/MEDIUM/HIGH"
    )
    risk_mitigation = Column(
        Text,
        comment="风险缓解措施"
    )
    
    # === AI生成信息 ===
    ai_confidence_score = Column(
        Numeric(5, 2),
        comment="AI建议置信度（0-100）"
    )
    ai_reasoning = Column(
        Text,
        comment="AI推理过程"
    )
    similar_cases = Column(
        JSON,
        comment="类似案例参考（JSON数组）"
    )
    # 示例：
    # [
    #   {
    #     "project": "PRJ-2025-088",
    #     "situation": "相似的供应链问题",
    #     "action_taken": "更换供应商",
    #     "result": "节约8%成本"
    #   }
    # ]
    
    # === 实施状态跟踪 ===
    status = Column(
        String(20),
        default="PENDING",
        comment="状态：PENDING/APPROVED/REJECTED/IN_PROGRESS/COMPLETED/CANCELLED"
    )
    
    # 审批流程
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        comment="审核人ID"
    )
    reviewed_at = Column(
        DateTime,
        comment="审核时间"
    )
    review_decision = Column(
        String(20),
        comment="审核决定：APPROVED/REJECTED/NEED_MORE_INFO"
    )
    review_comments = Column(
        Text,
        comment="审核意见"
    )
    
    # 实施跟踪
    assigned_to = Column(
        Integer,
        ForeignKey("users.id"),
        comment="责任人ID"
    )
    start_date = Column(
        Date,
        comment="开始日期"
    )
    target_completion_date = Column(
        Date,
        comment="目标完成日期"
    )
    actual_completion_date = Column(
        Date,
        comment="实际完成日期"
    )
    
    # 实施结果
    actual_cost_saving = Column(
        Numeric(18, 4),
        comment="实际成本节约"
    )
    actual_implementation_cost = Column(
        Numeric(18, 4),
        comment="实际实施成本"
    )
    effectiveness_rating = Column(
        Integer,
        comment="有效性评分（1-5星）"
    )
    lessons_learned = Column(
        Text,
        comment="经验教训"
    )
    
    # === 附加信息 ===
    tags = Column(
        JSON,
        comment="标签（便于分类和搜索）"
    )
    # 示例：["供应链优化", "成本削减", "紧急"]
    
    attachments = Column(
        JSON,
        comment="附件列表（JSON数组）"
    )
    # 示例：[{"name": "分析报告.pdf", "url": "...", "type": "pdf"}]
    
    # 备注
    notes = Column(Text, comment="备注")
    
    # 创建人
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        comment="创建人ID"
    )
    
    # 关系
    prediction = relationship("CostPrediction", back_populates="optimization_suggestions")
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    assignee = relationship("User", foreign_keys=[assigned_to])

    __table_args__ = (
        Index("idx_opt_sug_prediction", "prediction_id"),
        Index("idx_opt_sug_project", "project_id"),
        Index("idx_opt_sug_status", "status"),
        Index("idx_opt_sug_priority", "priority"),
        Index("idx_opt_sug_type", "suggestion_type"),
        Index("idx_opt_sug_assigned", "assigned_to"),
        {"comment": "成本优化建议表（AI生成）"}
    )

    def __repr__(self):
        return f"<CostOptimizationSuggestion {self.suggestion_code} saving={self.estimated_cost_saving}>"
