# -*- coding: utf-8 -*-
"""
项目风险历史模型

记录项目风险等级的变更历史，用于追踪和分析。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ProjectRiskHistory(Base, TimestampMixin):
    """项目风险历史表

    记录项目风险等级的自动升级历史，包含：
    - 风险等级变化（旧→新）
    - 触发风险计算的因子
    - 触发来源（系统自动/手动）
    """

    __tablename__ = "project_risk_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 风险等级变化
    old_risk_level = Column(String(20), comment="原风险等级: LOW/MEDIUM/HIGH/CRITICAL")
    new_risk_level = Column(String(20), comment="新风险等级: LOW/MEDIUM/HIGH/CRITICAL")

    # 风险因子（JSON格式存储详细数据）
    risk_factors = Column(JSON, comment="风险因子详情")

    # 触发信息
    triggered_by = Column(String(50), default="SYSTEM", comment="触发者：SYSTEM/MANUAL/用户ID")
    triggered_at = Column(DateTime, default=datetime.now, comment="触发时间")

    # 备注
    remarks = Column(Text, comment="备注说明")

    # 关系
    project = relationship("Project", backref="risk_history")

    __table_args__ = (
        Index("idx_project_risk_history_project", "project_id"),
        Index("idx_project_risk_history_triggered_at", "triggered_at"),
        Index("idx_project_risk_history_level", "new_risk_level"),
        {"comment": "项目风险历史表"}
    )

    def __repr__(self):
        return f"<ProjectRiskHistory(project_id={self.project_id}, {self.old_risk_level} -> {self.new_risk_level})>"


class ProjectRiskSnapshot(Base, TimestampMixin):
    """项目风险快照表

    定期保存项目的风险状态快照，用于趋势分析。
    """

    __tablename__ = "project_risk_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 快照时间
    snapshot_date = Column(DateTime, nullable=False, comment="快照日期")

    # 风险等级
    risk_level = Column(String(20), comment="风险等级")

    # 风险指标
    overdue_milestones_count = Column(Integer, default=0, comment="逾期里程碑数")
    total_milestones_count = Column(Integer, default=0, comment="总里程碑数")
    overdue_tasks_count = Column(Integer, default=0, comment="逾期任务数")
    open_risks_count = Column(Integer, default=0, comment="未关闭风险数")
    high_risks_count = Column(Integer, default=0, comment="高风险数")

    # 详细数据
    risk_factors = Column(JSON, comment="风险因子详情")

    # 关系
    project = relationship("Project", backref="risk_snapshots")

    __table_args__ = (
        Index("idx_project_risk_snapshot_project", "project_id"),
        Index("idx_project_risk_snapshot_date", "snapshot_date"),
        {"comment": "项目风险快照表"}
    )
