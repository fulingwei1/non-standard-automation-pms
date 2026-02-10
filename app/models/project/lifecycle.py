# -*- coding: utf-8 -*-
"""
项目生命周期模型 - ProjectStage, ProjectStatus, ProjectStatusLog
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ProjectStage(Base, TimestampMixin):
    """
    项目阶段表（项目相关）

    管理项目的9个生命周期阶段（S1-S9）：
    - S1: 需求进入
    - S2: 方案设计
    - S3: 采购备料
    - S4: 加工制造
    - S5: 装配调试
    - S6: 出厂验收 (FAT)
    - S7: 包装发运
    - S8: 现场安装 (SAT)
    - S9: 质保结项

    每个阶段包含：
    - 计划与实际时间
    - 进度百分比
    - 门控条件和必需交付物
    - 默认工期
    """

    __tablename__ = "project_stages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="所属项目"
    )
    stage_code = Column(String(20), nullable=False, comment="阶段编码：S1-S9")
    stage_name = Column(String(50), nullable=False, comment="阶段名称")
    stage_order = Column(Integer, nullable=False, comment="阶段顺序")
    description = Column(Text, comment="阶段描述")

    # 计划与实际
    planned_start_date = Column(Date, comment="计划开始")
    planned_end_date = Column(Date, comment="计划结束")
    actual_start_date = Column(Date, comment="实际开始")
    actual_end_date = Column(Date, comment="实际结束")

    # 进度
    progress_pct = Column(Integer, default=0, comment="进度(%)")
    status = Column(String(20), default="PENDING", comment="状态")

    # 门控条件
    gate_conditions = Column(Text, comment="进入条件JSON")
    required_deliverables = Column(Text, comment="必需交付物JSON")

    # 默认时长
    default_duration_days = Column(Integer, comment="默认工期（天）")

    # 颜色配置
    color = Column(String(20), comment="显示颜色")
    icon = Column(String(50), comment="图标")

    is_active = Column(Boolean, default=True)

    # 关系
    project = relationship("Project", back_populates="stages")
    statuses = relationship("ProjectStatus", back_populates="stage", lazy="dynamic")

    __table_args__ = (
        Index("idx_stage_project", "project_id"),
        Index("idx_stage_project_code", "project_id", "stage_code", unique=True),
    )

    @property
    def is_completed(self) -> bool:
        """阶段是否已完成"""
        return self.actual_end_date is not None

    @property
    def is_overdue(self) -> bool:
        """阶段是否逾期"""
        if not self.planned_end_date or self.actual_end_date:
            return False
        return self.actual_end_date > self.planned_end_date

    @property
    def duration_days(self) -> int:
        """实际持续天数"""
        if self.actual_start_date and self.actual_end_date:
            return (self.actual_end_date - self.actual_start_date).days
        return 0

    def __repr__(self):
        return f"<ProjectStage {self.stage_code}>"


class ProjectStatus(Base, TimestampMixin):
    """项目状态定义表"""

    __tablename__ = "project_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(
        Integer, ForeignKey("project_stages.id"), nullable=False, comment="所属阶段ID"
    )
    status_code = Column(String(20), nullable=False, comment="状态编码")
    status_name = Column(String(50), nullable=False, comment="状态名称")
    status_order = Column(Integer, nullable=False, comment="状态顺序")
    description = Column(Text, comment="状态描述")

    # 状态类型
    status_type = Column(String(20), default="NORMAL", comment="NORMAL/MILESTONE/GATE")

    # 自动流转
    auto_next_status = Column(String(20), comment="自动下一状态")

    is_active = Column(Boolean, default=True)

    # 关系
    stage = relationship("ProjectStage", back_populates="statuses")

    __table_args__ = (
        Index("idx_project_statuses_stage", "stage_id"),
        Index("idx_project_statuses_stage_code", "stage_id", "status_code", unique=True),
    )

    def __repr__(self):
        return f"<ProjectStatus {self.status_code}>"


class ProjectStatusLog(Base):
    """项目状态变更日志表"""

    __tablename__ = "project_status_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(
        Integer, ForeignKey("machines.id"), nullable=True, comment="设备ID（可选）"
    )

    # 变更前状态
    old_stage = Column(String(20), comment="变更前阶段")
    old_status = Column(String(20), comment="变更前状态")
    old_health = Column(String(10), comment="变更前健康度")

    # 变更后状态
    new_stage = Column(String(20), comment="变更后阶段")
    new_status = Column(String(20), comment="变更后状态")
    new_health = Column(String(10), comment="变更后健康度")

    # 变更信息
    change_type = Column(
        String(20), nullable=True, comment="变更类型：STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE"
    )
    change_reason = Column(Text, comment="变更原因")
    change_note = Column(Text, comment="变更备注")

    # 操作信息
    changed_by = Column(Integer, ForeignKey("users.id"), comment="变更人ID")
    changed_at = Column(DateTime, nullable=False, comment="变更时间")

    # 关系
    project = relationship("Project", backref="status_logs")
    machine = relationship("Machine", backref="status_logs")
    changer = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        Index("idx_project_status_logs_project", "project_id"),
        Index("idx_project_status_logs_machine", "machine_id"),
        Index("idx_project_status_logs_time", "changed_at"),
    )

    def __repr__(self):
        return f"<ProjectStatusLog {self.change_type} for Project {self.project_id}>"
