# -*- coding: utf-8 -*-
"""
项目-变更单联动集成模型

关联表：project_change_impacts
记录 ECN 对项目的影响评估结果和执行联动记录
"""

from sqlalchemy import (
    JSON,
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
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ProjectChangeImpact(Base, TimestampMixin):
    """
    项目变更影响记录表

    双向关联：ECN → 项目，项目 → ECN
    生命周期：ECN 审批时创建（影响评估），ECN 执行后更新（联动结果）
    """

    __tablename__ = "project_change_impacts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 双向关联 ──
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")
    ecn_no = Column(String(50), nullable=False, comment="ECN编号（冗余，便于查询）")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID（可选）")

    # ── 评估阶段（ECN 审批时填写）──
    # 项目当前状态快照
    project_stage_snapshot = Column(String(20), comment="评估时项目阶段快照")
    project_progress_snapshot = Column(Numeric(5, 2), comment="评估时项目进度快照(%)")

    # 进度影响
    schedule_impact_days = Column(Integer, default=0, comment="预计延期天数")
    affected_milestones = Column(JSON, comment="受影响的里程碑列表")
    # 格式: [{"milestone_id": 1, "name": "FAT", "original_date": "2025-03-01", "new_date": "2025-03-15", "delay_days": 14}]

    # 成本影响
    rework_cost = Column(Numeric(14, 2), default=0, comment="返工成本")
    scrap_cost = Column(Numeric(14, 2), default=0, comment="报废成本")
    additional_cost = Column(Numeric(14, 2), default=0, comment="新增成本（新物料/工装等）")
    total_cost_impact = Column(Numeric(14, 2), default=0, comment="总成本影响")

    # 成本明细
    cost_breakdown = Column(JSON, comment="成本明细")
    # 格式: {"rework_hours": 40, "hourly_rate": 150, "scrap_materials": [...], "new_materials": [...]}

    # 风险评估
    risk_level = Column(String(20), default="LOW", comment="风险等级: LOW/MEDIUM/HIGH/CRITICAL")
    risk_description = Column(Text, comment="风险描述")

    # 综合影响报告
    impact_summary = Column(Text, comment="影响评估报告摘要")
    impact_report = Column(JSON, comment="完整影响报告（结构化）")
    # 格式: {"schedule": {...}, "cost": {...}, "risk": {...}, "recommendation": "..."}

    assessed_by = Column(Integer, ForeignKey("users.id"), comment="评估人")
    assessed_at = Column(DateTime, comment="评估时间")

    # ── 执行阶段（ECN 执行后填写）──
    # 里程碑更新
    milestones_updated = Column(Boolean, default=False, comment="里程碑是否已更新")
    milestone_update_detail = Column(JSON, comment="里程碑更新明细")

    # 成本记录
    costs_recorded = Column(Boolean, default=False, comment="成本是否已记录")
    cost_record_ids = Column(JSON, comment="关联的项目成本记录ID列表")

    # 风险记录
    risk_created = Column(Boolean, default=False, comment="风险记录是否已创建")
    risk_record_id = Column(Integer, comment="关联的项目风险记录ID")

    # 实际影响（执行后回填）
    actual_delay_days = Column(Integer, comment="实际延期天数")
    actual_cost_impact = Column(Numeric(14, 2), comment="实际成本影响")

    # 状态
    status = Column(
        String(20),
        default="ASSESSED",
        comment="状态: ASSESSED(已评估)/EXECUTING(执行中)/COMPLETED(已完成)/CANCELLED(已取消)",
    )

    executed_by = Column(Integer, ForeignKey("users.id"), comment="执行人")
    executed_at = Column(DateTime, comment="执行完成时间")

    remark = Column(Text, comment="备注")

    # ── 关系 ──
    ecn = relationship("Ecn", foreign_keys=[ecn_id])
    project = relationship("Project", foreign_keys=[project_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    assessor = relationship("User", foreign_keys=[assessed_by])
    executor = relationship("User", foreign_keys=[executed_by])

    __table_args__ = (
        Index("idx_pci_ecn", "ecn_id"),
        Index("idx_pci_project", "project_id"),
        Index("idx_pci_ecn_project", "ecn_id", "project_id"),
        Index("idx_pci_status", "status"),
        Index("idx_pci_risk_level", "risk_level"),
        {"comment": "项目变更影响记录表"},
    )

    def __repr__(self):
        return f"<ProjectChangeImpact ecn={self.ecn_no} project={self.project_id}>"
