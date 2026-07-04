# -*- coding: utf-8 -*-
"""现场调试任务、签到和问题记录模型。"""

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class FieldTask(Base, TimestampMixin):
    """现场调试任务表。"""

    __tablename__ = "field_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_no = Column(String(50), unique=True, nullable=False, comment="现场任务编号")
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    address = Column(String(500), nullable=False, comment="现场地址")
    status = Column(String(20), default="pending", comment="状态")
    assigned_to = Column(String(100), comment="负责人")
    scheduled_date = Column(Date, comment="计划日期")
    progress = Column(Integer, default=0, comment="进度百分比")
    progress_note = Column(Text, comment="进度/完工说明")
    completion_signature = Column(Text, comment="完工签名")
    completion_time = Column(DateTime, comment="完工时间")

    checkins = relationship("FieldCheckin", back_populates="task")
    issues = relationship("FieldIssue", back_populates="task")

    __table_args__ = (
        Index("idx_field_tasks_status", "status"),
        Index("idx_field_tasks_assigned_to", "assigned_to"),
        Index("idx_field_tasks_scheduled_date", "scheduled_date"),
    )


class FieldCheckin(Base, TimestampMixin):
    """现场调试签到记录表。"""

    __tablename__ = "field_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("field_tasks.id"), nullable=False, comment="任务ID")
    user_id = Column(String(100), nullable=False, comment="签到用户")
    latitude = Column(Float, nullable=False, comment="纬度")
    longitude = Column(Float, nullable=False, comment="经度")
    checkin_time = Column(DateTime, comment="签到时间")

    task = relationship("FieldTask", back_populates="checkins")

    __table_args__ = (Index("idx_field_checkins_task_id", "task_id"),)


class FieldIssue(Base, TimestampMixin):
    """现场调试问题记录表。"""

    __tablename__ = "field_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("field_tasks.id"), nullable=False, comment="任务ID")
    description = Column(Text, nullable=False, comment="问题描述")
    photo_url = Column(Text, comment="现场图片")
    severity = Column(String(20), default="medium", comment="严重程度")
    status = Column(String(20), default="open", comment="状态")
    reported_by = Column(String(100), comment="上报人")
    reported_at = Column(DateTime, comment="上报时间")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution_note = Column(Text, comment="解决说明")

    task = relationship("FieldTask", back_populates="issues")

    __table_args__ = (
        Index("idx_field_issues_task_id", "task_id"),
        Index("idx_field_issues_status", "status"),
        Index("idx_field_issues_severity", "severity"),
    )
