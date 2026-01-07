"""
数据库模型定义 - SQLAlchemy ORM
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text
from sqlalchemy import ForeignKey, Index, Boolean, Numeric, SmallInteger
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Project(Base):
    """项目主表"""
    __tablename__ = "project"
    
    project_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="项目ID")
    project_code = Column(String(30), unique=True, nullable=False, comment="项目编号")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    project_type = Column(String(20), default="订单", comment="项目类型")
    project_level = Column(String(10), default="B", comment="项目等级")
    
    contract_id = Column(BigInteger, nullable=True, comment="关联合同ID")
    customer_id = Column(BigInteger, nullable=False, comment="客户ID")
    customer_name = Column(String(100), nullable=False, comment="客户名称")
    
    # 铁三角
    pm_id = Column(BigInteger, nullable=False, comment="项目经理ID")
    pm_name = Column(String(50), nullable=False, comment="项目经理姓名")
    te_id = Column(BigInteger, nullable=True, comment="技术经理ID")
    te_name = Column(String(50), nullable=True, comment="技术经理姓名")
    sc_id = Column(BigInteger, nullable=True, comment="供应链经理ID")
    sc_name = Column(String(50), nullable=True, comment="供应链经理姓名")
    
    # 日期
    plan_start_date = Column(Date, nullable=False, comment="计划开始日期")
    plan_end_date = Column(Date, nullable=False, comment="计划结束日期")
    baseline_start_date = Column(Date, nullable=True, comment="基线开始日期")
    baseline_end_date = Column(Date, nullable=True, comment="基线结束日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    
    # 工期工时
    plan_duration = Column(Integer, default=0, comment="计划工期（工作日）")
    plan_manhours = Column(Numeric(10, 2), default=0, comment="计划总工时")
    actual_manhours = Column(Numeric(10, 2), default=0, comment="已消耗工时")
    
    # 进度
    progress_rate = Column(Numeric(5, 2), default=0, comment="进度完成率%")
    plan_progress_rate = Column(Numeric(5, 2), default=0, comment="计划进度率%")
    spi = Column(Numeric(5, 2), default=1.00, comment="进度绩效指数")
    
    # 阶段状态
    current_phase = Column(String(30), default="立项启动", comment="当前阶段")
    status = Column(String(20), default="未启动", comment="项目状态")
    health_status = Column(String(10), default="绿", comment="健康状态")
    
    # 系统字段
    created_by = Column(BigInteger, nullable=False, comment="创建人ID")
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_by = Column(BigInteger, nullable=True, comment="更新人ID")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, comment="是否删除")
    
    # 关系
    tasks = relationship("WbsTask", back_populates="project")
    
    __table_args__ = (
        Index("idx_project_customer", "customer_id"),
        Index("idx_project_pm", "pm_id"),
        Index("idx_project_status", "status"),
    )


class WbsTask(Base):
    """WBS任务表"""
    __tablename__ = "wbs_task"
    
    task_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    project_id = Column(BigInteger, ForeignKey("project.project_id"), nullable=False, comment="项目ID")
    wbs_code = Column(String(20), nullable=False, comment="WBS编码")
    task_name = Column(String(200), nullable=False, comment="任务名称")
    
    # 层级
    parent_id = Column(BigInteger, nullable=True, comment="父任务ID")
    level = Column(SmallInteger, default=1, comment="层级")
    sort_order = Column(Integer, default=0, comment="排序号")
    path = Column(String(200), nullable=True, comment="层级路径")
    
    # 分类
    phase = Column(String(30), nullable=False, comment="所属阶段")
    task_type = Column(String(30), nullable=False, comment="任务类型")
    
    # 日期
    plan_start_date = Column(Date, nullable=False, comment="计划开始日期")
    plan_end_date = Column(Date, nullable=False, comment="计划结束日期")
    baseline_start_date = Column(Date, nullable=True, comment="基线开始日期")
    baseline_end_date = Column(Date, nullable=True, comment="基线结束日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    
    # 工期工时
    plan_duration = Column(Integer, default=1, comment="计划工期")
    plan_manhours = Column(Numeric(10, 2), default=0, comment="计划工时")
    actual_manhours = Column(Numeric(10, 2), default=0, comment="实际工时")
    
    # 进度
    progress_rate = Column(Numeric(5, 2), default=0, comment="进度完成率%")
    progress_method = Column(String(20), default="工时法", comment="进度计算方式")
    weight = Column(Numeric(5, 2), default=1.00, comment="权重")
    
    # 负责人
    owner_id = Column(BigInteger, nullable=True, comment="主负责人ID")
    owner_name = Column(String(50), nullable=True, comment="主负责人姓名")
    owner_dept_id = Column(BigInteger, nullable=True, comment="负责部门ID")
    owner_dept_name = Column(String(50), nullable=True, comment="负责部门")
    
    # 关键路径
    is_critical = Column(SmallInteger, default=0, comment="是否关键路径")
    is_milestone = Column(SmallInteger, default=0, comment="是否里程碑")
    float_days = Column(Integer, default=0, comment="浮动时间")
    earliest_start = Column(Date, nullable=True, comment="最早开始")
    latest_finish = Column(Date, nullable=True, comment="最迟完成")
    
    # 状态
    status = Column(String(20), default="未开始", comment="状态")
    block_reason = Column(String(200), nullable=True, comment="阻塞原因")
    block_type = Column(String(30), nullable=True, comment="阻塞类型")
    
    # 交付物
    deliverable = Column(String(500), nullable=True, comment="交付物")
    priority = Column(SmallInteger, default=3, comment="优先级")
    
    # 系统字段
    created_by = Column(BigInteger, nullable=False, comment="创建人ID")
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, comment="是否删除")
    
    # 关系
    project = relationship("Project", back_populates="tasks")
    assignments = relationship("TaskAssignment", back_populates="task")
    
    __table_args__ = (
        Index("idx_task_project", "project_id"),
        Index("idx_task_parent", "parent_id"),
        Index("idx_task_owner", "owner_id"),
        Index("idx_task_status", "status"),
    )


class TaskAssignment(Base):
    """任务分配表"""
    __tablename__ = "task_assignment"
    
    assign_id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("wbs_task.task_id"), nullable=False)
    project_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(50), nullable=False)
    dept_id = Column(BigInteger, nullable=False)
    dept_name = Column(String(50), nullable=False)
    role = Column(String(20), default="参与人", comment="角色")
    
    plan_manhours = Column(Numeric(10, 2), default=0)
    actual_manhours = Column(Numeric(10, 2), default=0)
    remaining_manhours = Column(Numeric(10, 2), default=0)
    
    plan_start_date = Column(Date, nullable=False)
    plan_end_date = Column(Date, nullable=False)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    
    progress_rate = Column(Numeric(5, 2), default=0)
    status = Column(String(20), default="未开始")
    priority = Column(SmallInteger, default=3)
    
    assigned_by = Column(BigInteger, nullable=False)
    assigned_time = Column(DateTime, default=datetime.now)
    
    task = relationship("WbsTask", back_populates="assignments")
    
    __table_args__ = (
        Index("idx_assign_task", "task_id"),
        Index("idx_assign_user", "user_id"),
        Index("idx_assign_project", "project_id"),
    )


class TaskDependency(Base):
    """任务依赖表"""
    __tablename__ = "task_dependency"
    
    depend_id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False, comment="后置任务ID")
    predecessor_id = Column(BigInteger, nullable=False, comment="前置任务ID")
    project_id = Column(BigInteger, nullable=False)
    depend_type = Column(String(10), default="FS", comment="依赖类型")
    lag_days = Column(Integer, default=0, comment="延迟天数")
    created_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_depend_task", "task_id"),
        Index("idx_depend_pred", "predecessor_id"),
    )


class Timesheet(Base):
    """工时记录表"""
    __tablename__ = "timesheet"
    
    timesheet_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(50), nullable=False)
    dept_id = Column(BigInteger, nullable=False)
    work_date = Column(Date, nullable=False)
    project_id = Column(BigInteger, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    assign_id = Column(BigInteger, nullable=True)
    hours = Column(Numeric(4, 1), default=0)
    overtime_hours = Column(Numeric(4, 1), default=0)
    work_content = Column(String(500), nullable=True)
    status = Column(String(20), default="待审核")
    approved_by = Column(BigInteger, nullable=True)
    approved_time = Column(DateTime, nullable=True)
    created_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_ts_user_date", "user_id", "work_date"),
        Index("idx_ts_task", "task_id"),
    )


class TaskLog(Base):
    """任务日志表"""
    __tablename__ = "task_log"
    
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    project_id = Column(BigInteger, nullable=False)
    action = Column(String(50), nullable=False)
    field_name = Column(String(50), nullable=True)
    old_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    remark = Column(String(500), nullable=True)
    operator_id = Column(BigInteger, nullable=False)
    operator_name = Column(String(50), nullable=False)
    created_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_log_task", "task_id"),
        Index("idx_log_time", "created_time"),
    )


class ProgressAlert(Base):
    """进度预警表"""
    __tablename__ = "progress_alert"
    
    alert_id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    task_id = Column(BigInteger, nullable=True)
    alert_type = Column(String(50), nullable=False)
    alert_level = Column(String(10), nullable=False)
    alert_title = Column(String(200), nullable=False)
    alert_content = Column(Text, nullable=True)
    trigger_value = Column(String(100), nullable=True)
    threshold_value = Column(String(100), nullable=True)
    notify_users = Column(String(500), nullable=True)
    status = Column(String(20), default="待处理")
    handle_user_id = Column(BigInteger, nullable=True)
    handle_time = Column(DateTime, nullable=True)
    handle_remark = Column(String(500), nullable=True)
    created_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_alert_project", "project_id"),
        Index("idx_alert_status", "status"),
    )


class WorkloadSnapshot(Base):
    """工程师负荷快照表"""
    __tablename__ = "workload_snapshot"
    
    snapshot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(50), nullable=False)
    dept_id = Column(BigInteger, nullable=False)
    snapshot_date = Column(Date, nullable=False)
    period_type = Column(String(10), default="日")
    available_hours = Column(Numeric(10, 2), default=8)
    allocated_hours = Column(Numeric(10, 2), default=0)
    actual_hours = Column(Numeric(10, 2), default=0)
    allocation_rate = Column(Numeric(5, 2), default=0)
    task_count = Column(Integer, default=0)
    project_count = Column(Integer, default=0)
    created_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_snapshot_date", "snapshot_date"),
    )
