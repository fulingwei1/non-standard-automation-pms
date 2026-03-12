# -*- coding: utf-8 -*-
"""
方案版本模型

为 PresaleAISolution 提供版本控制能力。
每次方案修改生成新版本，不覆盖旧版本。
"""

from sqlalchemy import (
    DECIMAL,
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

from app.models.base import Base, TimestampMixin


class SolutionVersion(Base, TimestampMixin):
    """方案版本表

    核心设计：
    - 每个 PresaleAISolution 可以有多个版本
    - 版本号格式：V1.0, V1.1, V2.0（主版本.次版本）
    - 主版本号：approved 状态时递增
    - 次版本号：draft 状态下递增
    - 支持版本树结构（parent_version_id）
    """

    __tablename__ = "solution_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    solution_id = Column(
        Integer,
        ForeignKey("presale_ai_solution.id", ondelete="CASCADE"),
        nullable=False,
        comment="方案ID",
    )
    version_no = Column(String(20), nullable=False, comment="版本号，如 V1.0, V1.1")

    # === 方案内容（从 PresaleAISolution 迁移）===
    generated_solution = Column(JSON, comment="生成的完整方案 JSON 格式")
    architecture_diagram = Column(Text, comment="系统架构图 Mermaid 代码")
    topology_diagram = Column(Text, comment="设备拓扑图 Mermaid 代码")
    signal_flow_diagram = Column(Text, comment="信号流程图 Mermaid 代码")
    bom_list = Column(JSON, comment="BOM清单 JSON 格式")
    technical_parameters = Column(JSON, comment="技术参数表")
    process_flow = Column(Text, comment="工艺流程说明")
    solution_description = Column(Text, comment="方案描述")

    # === 变更信息 ===
    change_summary = Column(Text, comment="变更摘要")
    change_reason = Column(String(200), comment="变更原因")
    parent_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id", ondelete="SET NULL"),
        comment="父版本ID（用于版本树）",
    )

    # === 审批状态 ===
    status = Column(
        String(20),
        default="draft",
        nullable=False,
        comment="状态：draft/pending_review/approved/rejected",
    )
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comments = Column(Text, comment="审批意见")

    # === AI 元数据 ===
    ai_model_used = Column(String(100), comment="使用的AI模型")
    confidence_score = Column(DECIMAL(3, 2), comment="方案置信度评分 (0-1)")
    quality_score = Column(DECIMAL(3, 2), comment="方案质量评分 (0-5)")
    generation_time_seconds = Column(DECIMAL(6, 2), comment="生成耗时(秒)")
    prompt_tokens = Column(Integer, comment="Prompt tokens")
    completion_tokens = Column(Integer, comment="Completion tokens")

    # === 关系 ===
    # 方案主表
    solution = relationship(
        "PresaleAISolution",
        back_populates="versions",
        foreign_keys=[solution_id],
    )
    # 父版本（版本树结构）
    parent_version = relationship(
        "SolutionVersion",
        remote_side=[id],
        backref="child_versions",
    )
    # 审批人
    approver = relationship("User", foreign_keys=[approved_by])

    # 绑定的成本估算（反向引用，由 PresaleAICostEstimation 定义）
    # cost_estimations = relationship("PresaleAICostEstimation", back_populates="solution_version")

    # 绑定的报价版本（反向引用，由 QuoteVersion 定义）
    # quote_versions = relationship("QuoteVersion", back_populates="solution_version")

    __table_args__ = (
        Index("idx_sv_solution_id", "solution_id"),
        Index("idx_sv_status", "status"),
        Index("idx_sv_created_at", "created_at"),
        UniqueConstraint("solution_id", "version_no", name="uq_solution_version"),
        {"comment": "方案版本表"},
    )

    def __repr__(self):
        return f"<SolutionVersion {self.solution_id}-{self.version_no}>"

    @property
    def is_approved(self) -> bool:
        """是否已审批"""
        return self.status == "approved"

    @property
    def is_editable(self) -> bool:
        """是否可编辑（仅 draft 状态可编辑）"""
        return self.status == "draft"
