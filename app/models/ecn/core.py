# -*- coding: utf-8 -*-
"""
ECN模型 - 核心表
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class Ecn(Base, TimestampMixin):
    """ECN主表"""

    __tablename__ = "ecn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_no = Column(String(50), unique=True, nullable=False, comment="ECN编号")
    ecn_title = Column(String(200), nullable=False, comment="ECN标题")
    ecn_type = Column(String(20), nullable=True, comment="变更类型")

    # 来源
    source_type = Column(String(20), nullable=True, comment="来源类型")
    source_no = Column(String(100), comment="来源单号")
    source_id = Column(Integer, comment="来源ID")

    # 关联
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=True, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")

    # 变更内容
    change_reason = Column(Text, nullable=True, comment="变更原因")
    change_description = Column(Text, nullable=True, comment="变更内容描述")
    change_scope = Column(String(20), default="PARTIAL", comment="变更范围")

    # 优先级
    priority = Column(String(20), default="NORMAL", comment="优先级")
    urgency = Column(String(20), default="NORMAL", comment="紧急程度")

    # 影响评估
    cost_impact = Column(Numeric(14, 2), default=0, comment="成本影响")
    schedule_impact_days = Column(Integer, default=0, comment="工期影响(天)")
    quality_impact = Column(String(20), comment="质量影响")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态")
    current_step = Column(String(50), comment="当前步骤")

    # 申请人
    applicant_id = Column(Integer, ForeignKey("users.id"), comment="申请人")
    applicant_dept = Column(String(100), comment="申请部门")
    applied_at = Column(DateTime, comment="申请时间")

    # 审批结果
    approval_result = Column(String(20), comment="审批结果")
    approval_note = Column(Text, comment="审批意见")
    approved_at = Column(DateTime, comment="审批时间")

    # 执行
    execution_start = Column(DateTime, comment="执行开始")
    execution_end = Column(DateTime, comment="执行结束")
    execution_note = Column(Text, comment="执行说明")

    # RCA分析（根本原因分析）
    root_cause = Column(String(20), comment="根本原因类型")
    root_cause_analysis = Column(Text, comment="RCA分析内容")
    root_cause_category = Column(String(50), comment="原因分类")

    # 解决方案
    solution = Column(Text, comment="解决方案")
    solution_template_id = Column(Integer, comment="使用的解决方案模板ID")
    similar_ecn_ids = Column(JSON, comment="相似ECN ID列表")
    solution_source = Column(
        String(20), comment="解决方案来源：MANUAL/AUTO_EXTRACT/KNOWLEDGE_BASE"
    )

    # 关闭
    closed_at = Column(DateTime, comment="关闭时间")
    closed_by = Column(Integer, ForeignKey("users.id"), comment="关闭人")

    # 附件
    attachments = Column(JSON, comment="附件")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project")
    machine = relationship("Machine")
    applicant = relationship("User", foreign_keys=[applicant_id])
    evaluations = relationship("EcnEvaluation", back_populates="ecn", lazy="dynamic")
    approvals = relationship("EcnApproval", back_populates="ecn", lazy="dynamic")
    tasks = relationship("EcnTask", back_populates="ecn", lazy="dynamic")
    affected_materials = relationship(
        "EcnAffectedMaterial", back_populates="ecn", lazy="dynamic"
    )
    affected_orders = relationship(
        "EcnAffectedOrder", back_populates="ecn", lazy="dynamic"
    )
    bom_impacts = relationship("EcnBomImpact", back_populates="ecn", lazy="dynamic")
    responsibilities = relationship(
        "EcnResponsibility", back_populates="ecn", lazy="dynamic"
    )
    solution_template = relationship(
        "EcnSolutionTemplate",
        foreign_keys="EcnSolutionTemplate.source_ecn_id",
        uselist=False,
        back_populates="source_ecn",
    )
    logs = relationship("EcnLog", back_populates="ecn", lazy="dynamic")

    __table_args__ = (
        Index("idx_ecn_project", "project_id"),
        Index("idx_ecn_status", "status"),
        Index("idx_ecn_type", "ecn_type"),
        Index("idx_ecn_applicant", "applicant_id"),
    )

    def __repr__(self):
        return f"<Ecn {self.ecn_no}>"
