"""
售前AI成本估算模型

【重构】2026-03-12：
- 新增 solution_version_id，绑定方案版本
- 新增 version_no，支持同一方案版本多次估算
- 新增审批流程字段
- 新增绑定状态字段
"""

from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    Boolean,
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class PresaleAICostEstimation(Base):
    """AI成本估算记录表

    核心绑定规则：
    - 每个成本估算必须绑定一个方案版本（solution_version_id）
    - 同一方案版本可以有多个成本估算版本（version_no）
    - 只有 approved 状态的成本估算可以被报价引用
    """

    __tablename__ = "presale_ai_cost_estimation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    presale_ticket_id = Column(Integer, nullable=False, index=True, comment="售前工单ID")

    # === 【保留】原字段，用于向后兼容 ===
    solution_id = Column(Integer, nullable=True, comment="解决方案ID（废弃，使用 solution_version_id）")

    # === 【新增】方案版本绑定 ===
    solution_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id", ondelete="SET NULL"),
        nullable=True,  # 迁移期间允许为空，后续改为 nullable=False
        comment="方案版本ID（绑定到具体版本）",
    )
    version_no = Column(String(20), default="V1", comment="成本估算版本号")

    # 成本分解
    hardware_cost = Column(DECIMAL(12, 2), nullable=True, comment="硬件成本(BOM)")
    software_cost = Column(DECIMAL(12, 2), nullable=True, comment="软件成本(开发工时)")
    installation_cost = Column(DECIMAL(12, 2), nullable=True, comment="安装调试成本")
    service_cost = Column(DECIMAL(12, 2), nullable=True, comment="售后服务成本")
    risk_reserve = Column(DECIMAL(12, 2), nullable=True, comment="风险储备金")
    total_cost = Column(DECIMAL(12, 2), nullable=False, comment="总成本")

    # AI分析结果
    optimization_suggestions = Column(JSON, nullable=True, comment="成本优化建议")
    pricing_recommendations = Column(JSON, nullable=True, comment="定价推荐(low/medium/high)")
    confidence_score = Column(DECIMAL(3, 2), nullable=True, comment="置信度评分(0-1)")

    # AI模型信息
    model_version = Column(String(50), nullable=True, comment="AI模型版本")
    input_parameters = Column(JSON, nullable=True, comment="输入参数快照")

    # === 【新增】审批流程 ===
    status = Column(
        String(20),
        default="draft",
        nullable=False,
        comment="状态：draft/pending_review/approved/rejected",
    )
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comments = Column(Text, comment="审批意见")

    # === 【新增】绑定状态 ===
    is_bound_to_quote = Column(Boolean, default=False, comment="是否已绑定报价")
    bound_quote_version_id = Column(Integer, comment="绑定的报价版本ID（反向引用，非外键）")

    # 元数据
    created_by = Column(Integer, nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # === 关系 ===
    solution_version = relationship(
        "SolutionVersion",
        backref="cost_estimations",
        foreign_keys=[solution_version_id],
    )
    approver = relationship("User", foreign_keys=[approved_by])

    # 索引
    __table_args__ = (
        Index("idx_presale_ticket_id", "presale_ticket_id"),
        Index("idx_cost_est_created_at", "created_at"),
        Index("idx_ce_solution_version", "solution_version_id"),
        Index("idx_ce_status", "status"),
        UniqueConstraint(
            "solution_version_id", "version_no",
            name="uq_cost_estimation_version",
        ),
    )


class PresaleCostHistory(Base):
    """历史成本数据(用于学习)"""

    __tablename__ = "presale_cost_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=True, comment="项目ID")
    project_name = Column(String(200), nullable=True, comment="项目名称")

    # 成本对比
    estimated_cost = Column(DECIMAL(12, 2), nullable=False, comment="估算成本")
    actual_cost = Column(DECIMAL(12, 2), nullable=False, comment="实际成本")
    variance_rate = Column(DECIMAL(5, 2), nullable=True, comment="偏差率(%)")

    # 详细分解
    cost_breakdown = Column(JSON, nullable=True, comment="成本分解详情")
    variance_analysis = Column(JSON, nullable=True, comment="偏差分析详情")

    # 项目特征(用于机器学习)
    project_features = Column(JSON, nullable=True, comment="项目特征向量")

    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引
    __table_args__ = (
        Index("idx_cost_hist_project", "project_id"),
        Index("idx_cost_hist_created_at", "created_at"),
    )


class PresaleCostOptimizationRecord(Base):
    """成本优化建议记录

    【状态】未启用 - 成本优化记录"""

    __tablename__ = "presale_cost_optimization_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estimation_id = Column(Integer, ForeignKey("presale_ai_cost_estimation.id"), nullable=False)

    # 优化建议
    optimization_type = Column(
        String(50), nullable=False, comment="优化类型(hardware/software/installation/service)"
    )
    original_cost = Column(DECIMAL(12, 2), nullable=False, comment="原始成本")
    optimized_cost = Column(DECIMAL(12, 2), nullable=False, comment="优化后成本")
    saving_amount = Column(DECIMAL(12, 2), nullable=False, comment="节省金额")
    saving_rate = Column(DECIMAL(5, 2), nullable=False, comment="节省比例(%)")

    # 建议详情
    suggestion_detail = Column(JSON, nullable=True, comment="优化建议详情")
    alternative_solutions = Column(JSON, nullable=True, comment="替代方案")

    # 可行性评估
    feasibility_score = Column(DECIMAL(3, 2), nullable=True, comment="可行性评分(0-1)")
    risk_assessment = Column(Text, nullable=True, comment="风险评估")

    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关系
    estimation = relationship("PresaleAICostEstimation", backref="optimization_records")
