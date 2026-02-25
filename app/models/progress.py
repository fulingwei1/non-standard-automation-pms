# -*- coding: utf-8 -*-
"""
进度跟踪模块 ORM 模型
包含：WBS模板、模板任务、项目任务、任务依赖、进度日志、计划基线
"""

from datetime import datetime
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
)
from sqlalchemy.orm import relationship, synonym

from app.models.base import Base, TimestampMixin


class WbsTemplate(Base, TimestampMixin):
    """WBS模板表
    
    【状态】未启用 - WBS模板"""
    __tablename__ = "wbs_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_code = Column(String(20), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(100), nullable=False, comment="模板名称")
    project_type = Column(String(20), comment="项目类型")
    equipment_type = Column(String(20), comment="设备类型")
    version_no = Column(String(10), default="V1", comment="版本号")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    tasks = relationship("WbsTemplateTask", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wbs_template_code", "template_code"),
    )

    def __repr__(self):
        return f"<WbsTemplate {self.template_code}>"


class WbsTemplateTask(Base):
    """WBS模板任务表
    
    【状态】未启用 - WBS模板任务"""
    __tablename__ = "wbs_template_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_id = Column(Integer, ForeignKey("wbs_templates.id"), nullable=False, comment="模板ID")
    task_name = Column(String(200), comment="任务名称")
    stage = Column(String(20), comment="阶段（S1-S9）")
    default_owner_role = Column(String(50), comment="默认负责人角色")
    plan_days = Column(Integer, comment="计划天数")
    weight = Column(Numeric(5, 2), default=Decimal("1.00"), comment="权重")
    depends_on_template_task_id = Column(
        Integer, ForeignKey("wbs_template_tasks.id"), comment="依赖的模板任务ID"
    )

    # 关系
    template = relationship("WbsTemplate", back_populates="tasks")
    depends_on = relationship("WbsTemplateTask", remote_side=[id], backref="dependents")

    __table_args__ = (
        Index("idx_wbs_template_tasks_template", "template_id"),
    )

    def __repr__(self):
        return f"<WbsTemplateTask {self.task_name}>"


class Task(Base, TimestampMixin):
    """项目任务表"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="机台ID")
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), comment="里程碑ID")
    task_code = Column(String(50), comment="任务编码")
    task_name = Column(String(200), nullable=True, comment="任务名称")
    stage = Column(String(20), comment="阶段（S1-S9）")
    status = Column(String(20), default="TODO", comment="状态：TODO/IN_PROGRESS/BLOCKED/DONE/CANCELLED")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    plan_start = Column(Date, comment="计划开始日期")
    plan_end = Column(Date, comment="计划结束日期")
    actual_start = Column(Date, comment="实际开始日期")
    actual_end = Column(Date, comment="实际结束日期")
    progress_percent = Column(Integer, default=0, comment="进度百分比（0-100）")
    progress_pct = synonym("progress_percent")
    weight = Column(Numeric(5, 2), default=Decimal("1.00"), comment="权重")
    block_reason = Column(Text, comment="阻塞原因")

    # 关系
    project = relationship("Project", backref="tasks")
    machine = relationship("Machine", backref="tasks")
    milestone = relationship("ProjectMilestone", backref="tasks")
    owner = relationship("User", foreign_keys=[owner_id])
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    depends_on_tasks = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task"
    )
    progress_logs = relationship("ProgressLog", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_milestone", "milestone_id"),
        Index("idx_tasks_owner", "owner_id"),
        Index("idx_tasks_status", "status"),
    )

    def __repr__(self):
        return f"<Task {self.task_name}>"


class TaskDependency(Base):
    """任务依赖关系表"""
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, comment="任务ID")
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, comment="依赖的任务ID")
    dependency_type = Column(String(10), default="FS", comment="依赖类型：FS/SS/FF/SF")
    lag_days = Column(Integer, default=0, comment="滞后天数")

    # 关系
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="depends_on_tasks")

    __table_args__ = (
        Index("idx_task_deps_task", "task_id"),
        Index("idx_task_deps_depends", "depends_on_task_id"),
    )

    def __repr__(self):
        return f"<TaskDependency {self.task_id} -> {self.depends_on_task_id}>"


class ProgressLog(Base):
    """进度日志表"""
    __tablename__ = "progress_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, comment="任务ID")
    progress_percent = Column(Integer, comment="进度百分比")
    update_note = Column(Text, comment="更新说明")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人ID")
    updated_at = Column(DateTime, default=datetime.now, comment="更新时间")

    # 关系
    task = relationship("Task", back_populates="progress_logs")
    updater = relationship("User", foreign_keys=[updated_by])

    __table_args__ = (
        Index("idx_progress_logs_task", "task_id"),
    )

    def __repr__(self):
        return f"<ProgressLog task_id={self.task_id} progress={self.progress_percent}%>"


class ScheduleBaseline(Base, TimestampMixin):
    """计划基线表
    
    【状态】未启用 - 进度基线"""
    __tablename__ = "schedule_baselines"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    baseline_no = Column(String(10), default="V1", comment="基线编号")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    project = relationship("Project", backref="baselines")
    creator = relationship("User", foreign_keys=[created_by])
    baseline_tasks = relationship("BaselineTask", back_populates="baseline", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_schedule_baselines_project", "project_id"),
    )

    def __repr__(self):
        return f"<ScheduleBaseline {self.baseline_no}>"


class BaselineTask(Base):
    """基线任务快照表
    
    【状态】未启用 - 基线任务"""
    __tablename__ = "baseline_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    baseline_id = Column(Integer, ForeignKey("schedule_baselines.id"), nullable=False, comment="基线ID")
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, comment="任务ID")
    plan_start = Column(Date, comment="计划开始日期")
    plan_end = Column(Date, comment="计划结束日期")
    weight = Column(Numeric(5, 2), comment="权重")

    # 关系
    baseline = relationship("ScheduleBaseline", back_populates="baseline_tasks")
    task = relationship("Task")

    __table_args__ = (
        Index("idx_baseline_tasks_baseline", "baseline_id"),
    )

    def __repr__(self):
        return f"<BaselineTask baseline_id={self.baseline_id} task_id={self.task_id}>"


class ProgressReport(Base, TimestampMixin):
    """进度报告表"""
    __tablename__ = "progress_reports"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    report_type = Column(String(20), nullable=False, comment="报告类型：daily/weekly")
    report_date = Column(Date, nullable=False, comment="报告日期")

    # 关联信息（三选一或组合）
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="机台ID")
    task_id = Column(Integer, ForeignKey("tasks.id"), comment="任务ID")

    # 报告内容
    content = Column(Text, nullable=False, comment="报告内容")
    completed_work = Column(Text, comment="已完成工作")
    planned_work = Column(Text, comment="计划工作")
    issues = Column(Text, comment="问题与阻塞")
    next_plan = Column(Text, comment="下一步计划")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")

    # 关系
    project = relationship("Project", backref="progress_reports")
    machine = relationship("Machine", backref="progress_reports")
    task = relationship("Task", backref="progress_reports")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_progress_reports_project", "project_id"),
        Index("idx_progress_reports_machine", "machine_id"),
        Index("idx_progress_reports_task", "task_id"),
        Index("idx_progress_reports_date", "report_date"),
        Index("idx_progress_reports_type", "report_type"),
    )

    def __repr__(self):
        return f"<ProgressReport {self.report_type} {self.report_date}>"

