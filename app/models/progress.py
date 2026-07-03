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
from sqlalchemy import event
from sqlalchemy import text as sa_text
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import relationship, synonym, with_loader_criteria

from app.models.base import Base, TimestampMixin
from app.models.task_center import TaskUnified


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

    __table_args__ = (Index("idx_wbs_template_code", "template_code"),)

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

    __table_args__ = (Index("idx_wbs_template_tasks_template", "template_id"),)

    def __repr__(self):
        return f"<WbsTemplateTask {self.task_name}>"


# ---- 项目任务门面（2026-07-03 双任务表整合 P2/P3，见 TASK_UNIFICATION_DESIGN.md）----
# Task 不再映射独立的 tasks 表（旧表只读保留至 P4），而是 task_unified 的"项目任务视角"：
# - 列名映射：task_name→title、stage→project_stage、owner_id→assignee_id、
#   plan_start→plan_start_date、progress_percent→progress 等，既有消费方零改动；
# - 状态词汇双向翻译：Python 侧沿用 TODO/DONE/BLOCKED，存储侧为任务中心词汇
#   PENDING/COMPLETED/PAUSED（自定义 Comparator 让查询字面量一并翻译）；
# - 全局 PROJECT 过滤：Session do_orm_execute 注入 task_type='PROJECT'；
# - 写入默认值：before_insert 兜底 task_type/source/priority/task_code/负责人/项目冗余列。

_STATUS_TO_STORAGE = {"TODO": "PENDING", "DONE": "COMPLETED", "BLOCKED": "PAUSED"}
_STATUS_FROM_STORAGE = {v: k for k, v in _STATUS_TO_STORAGE.items()}


def _status_to_storage(value):
    return _STATUS_TO_STORAGE.get(value, value)


def _status_from_storage(value):
    return _STATUS_FROM_STORAGE.get(value, value)


class _TaskStatusComparator(Comparator):
    """让 Task.status == 'DONE' / .in_(['TODO', ...]) 的字面量自动翻译成存储词汇。"""

    def operate(self, op, *other, **kwargs):
        def _convert(value):
            if isinstance(value, str):
                return _status_to_storage(value)
            if isinstance(value, (list, tuple, set)):
                return type(value)(_convert(v) for v in value)
            return value

        return op(self.__clause_element__(), *[_convert(o) for o in other], **kwargs)


class Task(Base):
    """项目任务（task_unified 门面）"""

    __table__ = TaskUnified.__table__

    # 属性名 → task_unified 列映射（未列出的列按原名自动映射）
    task_name = __table__.c.title
    stage = __table__.c.project_stage
    owner_id = __table__.c.assignee_id
    plan_start = __table__.c.plan_start_date
    plan_end = __table__.c.plan_end_date
    actual_start = __table__.c.actual_start_date
    actual_end = __table__.c.actual_end_date
    progress_percent = __table__.c.progress
    _status = __table__.c.status

    progress_pct = synonym("progress_percent")

    @hybrid_property
    def status(self):
        return _status_from_storage(self._status)

    @status.inplace.setter
    def _status_setter(self, value):
        self._status = _status_to_storage(value)

    @status.inplace.comparator
    @classmethod
    def _status_comparator(cls):
        return _TaskStatusComparator(cls._status)

    # 关系（沿用原语义；Project.tasks 现聚焦 task_unified 中的项目任务）
    project = relationship(
        "Project", foreign_keys=[__table__.c.project_id], backref="tasks", overlaps=""
    )
    machine = relationship("Machine", foreign_keys=[__table__.c.machine_id], backref="tasks")
    milestone = relationship(
        "ProjectMilestone", foreign_keys=[__table__.c.milestone_id], backref="tasks"
    )
    owner = relationship("User", foreign_keys=[__table__.c.assignee_id])
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    depends_on_tasks = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
    )
    progress_logs = relationship("ProgressLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task {self.task_name}>"


@event.listens_for(Task, "before_insert")
def _project_task_insert_defaults(mapper, connection, target):
    """项目任务写入 task_unified 时补齐任务中心必填与冗余字段。"""
    from uuid import uuid4

    if not target.task_type:
        target.task_type = "PROJECT"
    if not target.source_type:
        target.source_type = "PROJECT"
        target.source_id = target.project_id
    if not target.priority:
        target.priority = "MEDIUM"
    if target.is_active is None:
        target.is_active = True
    if target.progress_percent is None:
        target.progress_percent = 0
    if not target._status:
        target._status = "PENDING"
    if not target.task_code:
        target.task_code = f"PT-{uuid4().hex[:10].upper()}"
    if not target.owner_id:
        pm_id = None
        if target.project_id:
            pm_id = connection.execute(
                sa_text("SELECT pm_id FROM projects WHERE id=:i"), {"i": target.project_id}
            ).scalar()
        target.owner_id = pm_id or target.created_by or 1
    if not target.assignee_name and target.owner_id:
        target.assignee_name = connection.execute(
            sa_text("SELECT COALESCE(real_name, username) FROM users WHERE id=:i"),
            {"i": target.owner_id},
        ).scalar()
    if target.project_id and not target.project_code:
        row = connection.execute(
            sa_text("SELECT project_code, project_name FROM projects WHERE id=:i"),
            {"i": target.project_id},
        ).first()
        if row:
            target.project_code, target.project_name = row[0], row[1]


@event.listens_for(OrmSession, "do_orm_execute")
def _project_task_global_criteria(execute_state):
    """所有经 ORM 的 Task 查询自动限定 task_type='PROJECT'（任务中心 TaskUnified 不受影响）。"""
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
    ):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                Task, lambda cls: cls.task_type == "PROJECT", include_aliases=True
            )
        )


class TaskDependency(Base):
    """任务依赖关系表"""

    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    task_id = Column(Integer, ForeignKey("task_unified.id"), nullable=False, comment="任务ID")
    depends_on_task_id = Column(
        Integer, ForeignKey("task_unified.id"), nullable=False, comment="依赖的任务ID"
    )
    dependency_type = Column(String(10), default="FS", comment="依赖类型：FS/SS/FF/SF")
    lag_days = Column(Integer, default=0, comment="滞后天数")

    # 关系
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship(
        "Task", foreign_keys=[depends_on_task_id], back_populates="depends_on_tasks"
    )

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
    task_id = Column(Integer, ForeignKey("task_unified.id"), nullable=False, comment="任务ID")
    progress_percent = Column(Integer, comment="进度百分比")
    update_note = Column(Text, comment="更新说明")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人ID")
    updated_at = Column(DateTime, default=datetime.now, comment="更新时间")

    # 关系
    task = relationship("Task", back_populates="progress_logs")
    updater = relationship("User", foreign_keys=[updated_by])

    __table_args__ = (Index("idx_progress_logs_task", "task_id"),)

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
    baseline_tasks = relationship(
        "BaselineTask", back_populates="baseline", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_schedule_baselines_project", "project_id"),)

    def __repr__(self):
        return f"<ScheduleBaseline {self.baseline_no}>"


class BaselineTask(Base):
    """基线任务快照表

    【状态】未启用 - 基线任务"""

    __tablename__ = "baseline_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    baseline_id = Column(
        Integer, ForeignKey("schedule_baselines.id"), nullable=False, comment="基线ID"
    )
    task_id = Column(Integer, ForeignKey("task_unified.id"), nullable=False, comment="任务ID")
    plan_start = Column(Date, comment="计划开始日期")
    plan_end = Column(Date, comment="计划结束日期")
    weight = Column(Numeric(5, 2), comment="权重")

    # 关系
    baseline = relationship("ScheduleBaseline", back_populates="baseline_tasks")
    task = relationship("Task")

    __table_args__ = (Index("idx_baseline_tasks_baseline", "baseline_id"),)

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
    task_id = Column(Integer, ForeignKey("task_unified.id"), comment="任务ID")

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
