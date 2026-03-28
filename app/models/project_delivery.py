# -*- coding: utf-8 -*-
"""
项目交付排产计划模型

用于售前/售后阶段的项目交付排产计划管理
支持细化到人员级别的任务分配、长周期采购、变更管理
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

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
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProjectDeliverySchedule(Base, TimestampMixin):
    """项目交付排产计划主表"""
    
    __tablename__ = "project_delivery_schedules"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_no = Column(String(50), unique=True, nullable=False, comment="计划编号 PDS-2026-001")
    schedule_name = Column(String(200), nullable=False, comment="计划名称")
    
    # 关联
    lead_id = Column(Integer, ForeignKey("leads.id"), comment="商机 ID（合同签订前）")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目 ID（合同签订后）")
    project_template_id = Column(Integer, ForeignKey("project_templates.id"), comment="项目模板 ID")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同 ID（签订后）")
    
    # 版本
    version = Column(String(20), default="V1.0", comment="版本号 V1.0, V1.1, V2.0")
    version_comment = Column(String(500), comment="版本说明")
    
    # 状态
    status = Column(
        String(20),
        default="DRAFT",
        comment="状态：DRAFT/FILLING/REVIEWING/CONFIRMED/CHANGED"
    )
    usage_type = Column(
        String(20),
        default="INTERNAL",
        comment="使用类型：INTERNAL/CUSTOMER/BOTH"
    )
    
    # 人员
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发起人 ID（项目经理）")
    initiator_name = Column(String(100), comment="发起人姓名")
    confirmed_by = Column(Integer, ForeignKey("users.id"), comment="确认人 ID")
    confirmed_at = Column(DateTime, comment="确认时间")
    
    # 合同相关
    contract_signed_at = Column(DateTime, comment="合同签订时间")
    is_pre_contract = Column(Boolean, default=True, comment="是否合同签订前创建")
    
    # 版本管理
    is_active = Column(Boolean, default=True, comment="是否当前有效版本")
    parent_version_id = Column(Integer, ForeignKey("project_delivery_schedules.id"), comment="父版本 ID")
    
    # 关系
    lead = relationship("Lead", foreign_keys=[lead_id])
    project = relationship("Project", foreign_keys=[project_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    initiator = relationship("User", foreign_keys=[initiator_id])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    parent_version = relationship(
        "ProjectDeliverySchedule",
        remote_side=[id],
        foreign_keys=[parent_version_id]
    )
    tasks = relationship("ProjectDeliveryTask", back_populates="schedule", cascade="all, delete-orphan")
    long_cycle_purchases = relationship(
        "ProjectDeliveryLongCyclePurchase",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    mechanical_designs = relationship(
        "ProjectDeliveryMechanicalDesign",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    change_logs = relationship(
        "ProjectDeliveryChangeLog",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_pds_lead", "lead_id"),
        Index("idx_pds_project", "project_id"),
        Index("idx_pds_status", "status"),
        Index("idx_pds_usage", "usage_type"),
        Index("idx_pds_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliverySchedule {self.schedule_no} {self.version}>"


class ProjectDeliveryTask(Base, TimestampMixin):
    """交付任务表（细化到人员）"""
    
    __tablename__ = "project_delivery_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_id = Column(
        Integer,
        ForeignKey("project_delivery_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排产计划 ID"
    )
    task_no = Column(String(50), comment="任务编号 T001, T002")
    
    # 任务信息
    task_type = Column(
        String(30),
        nullable=False,
        comment="任务类型：MECHANICAL/ELECTRICAL/SOFTWARE/PURCHASE/PRODUCTION"
    )
    task_name = Column(String(200), nullable=False, comment="任务名称")
    task_description = Column(Text, comment="任务描述")
    machine_name = Column(String(200), comment="机台名称")
    module_name = Column(String(200), comment="模块名称")
    
    # 任务分解
    parent_task_id = Column(
        Integer,
        ForeignKey("project_delivery_tasks.id"),
        comment="父任务 ID（支持 WBS 分解）"
    )
    level = Column(Integer, default=1, comment="任务层级 1/2/3")
    
    # 人员分配
    assigned_engineer_id = Column(Integer, ForeignKey("users.id"), comment="工程师 ID")
    assigned_engineer_name = Column(String(100), comment="工程师姓名")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门 ID")
    department_name = Column(String(100), comment="部门名称")
    
    # 时间（支持小时级别）
    planned_start = Column(Date, nullable=False, comment="计划开始日期")
    planned_end = Column(Date, nullable=False, comment="计划结束日期")
    estimated_hours = Column(Numeric(10, 2), default=0, comment="预估工时（小时）")
    
    # 依赖关系
    predecessor_tasks = Column(JSON, default=list, comment="前置任务 ID 列表")
    dependency_type = Column(String(10), default="FS", comment="依赖类型：FS/SS/FF/SF")
    lag_days = Column(Integer, default=0, comment="延迟天数")
    
    # 冲突检测
    has_conflict = Column(Boolean, default=False, comment="是否有冲突")
    conflict_details = Column(JSON, comment="冲突详情")
    
    # 状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/IN_PROGRESS/COMPLETED")
    progress_pct = Column(Numeric(5, 2), default=0, comment="进度百分比 0-100")
    
    # 填写人
    filled_by = Column(Integer, ForeignKey("users.id"), comment="填写人 ID（部门人员）")
    filled_by_name = Column(String(100), comment="填写人姓名")
    filled_at = Column(DateTime, comment="填写时间")
    
    # 关系
    schedule = relationship("ProjectDeliverySchedule", back_populates="tasks")
    engineer = relationship("User", foreign_keys=[assigned_engineer_id])
    filler = relationship("User", foreign_keys=[filled_by])
    parent_task = relationship(
        "ProjectDeliveryTask",
        remote_side=[id],
        foreign_keys=[parent_task_id]
    )
    
    __table_args__ = (
        Index("idx_pdt_schedule", "schedule_id"),
        Index("idx_pdt_type", "task_type"),
        Index("idx_pdt_engineer", "assigned_engineer_id"),
        Index("idx_pdt_status", "status"),
        Index("idx_pdt_dates", "planned_start", "planned_end"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliveryTask {self.task_no} {self.task_name}>"


class ProjectDeliveryLongCyclePurchase(Base, TimestampMixin):
    """长周期采购清单（>60 天）"""
    
    __tablename__ = "project_delivery_long_cycle_purchases"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_id = Column(
        Integer,
        ForeignKey("project_delivery_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排产计划 ID"
    )
    item_no = Column(String(50), comment="物料编号 M001, M002")
    
    # 物料信息
    material_name = Column(String(200), nullable=False, comment="物料名称")
    material_spec = Column(String(500), comment="规格型号")
    material_category = Column(String(100), comment="物料分类")
    supplier = Column(String(200), comment="供应商")
    supplier_contact = Column(String(200), comment="供应商联系方式")
    
    # 时间
    lead_time_days = Column(Integer, nullable=False, comment="交期（天）")
    planned_order_date = Column(Date, comment="计划下单日期")
    planned_arrival_date = Column(Date, comment="计划到货日期")
    
    # 关键性
    is_critical = Column(Boolean, default=False, comment="是否关键物料")
    has_conflict = Column(Boolean, default=False, comment="是否有冲突（交期过长）")
    conflict_reason = Column(String(500), comment="冲突原因")
    
    # 填写人
    filled_by = Column(Integer, ForeignKey("users.id"), comment="填写人 ID（采购部人员）")
    filled_by_name = Column(String(100), comment="填写人姓名")
    filled_at = Column(DateTime, comment="填写时间")
    
    # 关系
    schedule = relationship("ProjectDeliverySchedule", back_populates="long_cycle_purchases")
    filler = relationship("User", foreign_keys=[filled_by])
    
    __table_args__ = (
        Index("idx_pdlcp_schedule", "schedule_id"),
        Index("idx_pdlcp_critical", "is_critical"),
        Index("idx_pdlcp_conflict", "has_conflict"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliveryLongCyclePurchase {self.item_no} {self.material_name}>"


class ProjectDeliveryMechanicalDesign(Base, TimestampMixin):
    """机械设计任务明细"""
    
    __tablename__ = "project_delivery_mechanical_designs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_id = Column(
        Integer,
        ForeignKey("project_delivery_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排产计划 ID"
    )
    
    # 设计信息
    design_type = Column(
        String(30),
        nullable=False,
        comment="设计类型：3D_DESIGN/2D_DRAFTING/BOM"
    )
    machine_name = Column(String(200), comment="机台名称")
    module_name = Column(String(200), comment="模块名称")
    
    # 人员
    designer_id = Column(Integer, ForeignKey("users.id"), comment="设计工程师 ID")
    designer_name = Column(String(100), comment="设计师姓名")
    
    # 时间
    planned_start = Column(Date, nullable=False, comment="计划开始")
    planned_end = Column(Date, nullable=False, comment="计划结束")
    estimated_hours = Column(Numeric(10, 2), default=0, comment="预估工时")
    
    # 交付物
    deliverables = Column(JSON, comment="交付物：[\"3D 模型\",\"装配图\"]")
    
    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    
    # 填写人
    filled_by = Column(Integer, ForeignKey("users.id"), comment="填写人 ID")
    filled_by_name = Column(String(100), comment="填写人姓名")
    filled_at = Column(DateTime, comment="填写时间")
    
    # 关系
    schedule = relationship("ProjectDeliverySchedule", back_populates="mechanical_designs")
    designer = relationship("User", foreign_keys=[designer_id])
    
    __table_args__ = (
        Index("idx_pdmd_schedule", "schedule_id"),
        Index("idx_pdmd_type", "design_type"),
        Index("idx_pdmd_designer", "designer_id"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliveryMechanicalDesign {self.design_type} {self.machine_name}>"


class ProjectDeliveryChangeLog(Base, TimestampMixin):
    """排产计划变更日志"""
    
    __tablename__ = "project_delivery_change_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_id = Column(
        Integer,
        ForeignKey("project_delivery_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排产计划 ID"
    )
    change_no = Column(String(50), comment="变更编号 CHG001, CHG002")
    
    # 变更类型
    change_type = Column(
        String(20),
        nullable=False,
        comment="变更类型：ADJUST/CONFIRM/CHANGE/VERSION"
    )
    
    # 版本
    version_from = Column(String(20), comment="变更前版本")
    version_to = Column(String(20), comment="变更后版本")
    
    # 变更内容
    old_data = Column(JSON, comment="变更前数据")
    new_data = Column(JSON, comment="变更后数据")
    change_reason = Column(String(500), comment="变更原因")
    change_description = Column(Text, comment="变更描述")
    
    # 人员
    changed_by = Column(Integer, ForeignKey("users.id"), comment="变更人 ID")
    changed_by_name = Column(String(100), comment="变更人姓名")
    changed_at = Column(DateTime, nullable=False, comment="变更时间")
    
    # 通知
    notified_users = Column(JSON, comment="已通知人员")
    notification_sent = Column(Boolean, default=False, comment="是否已通知")
    
    # 关系
    schedule = relationship("ProjectDeliverySchedule", back_populates="change_logs")
    changer = relationship("User", foreign_keys=[changed_by])
    
    __table_args__ = (
        Index("idx_pdcl_schedule", "schedule_id"),
        Index("idx_pdcl_type", "change_type"),
        Index("idx_pdcl_changed_at", "changed_at"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliveryChangeLog {self.change_no} {self.change_type}>"


class ProjectDeliveryDependency(Base, TimestampMixin):
    """任务依赖关系表"""
    
    __tablename__ = "project_delivery_dependencies"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    schedule_id = Column(
        Integer,
        ForeignKey("project_delivery_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排产计划 ID"
    )
    
    # 依赖关系
    predecessor_task_id = Column(
        Integer,
        ForeignKey("project_delivery_tasks.id"),
        nullable=False,
        comment="前置任务 ID"
    )
    successor_task_id = Column(
        Integer,
        ForeignKey("project_delivery_tasks.id"),
        nullable=False,
        comment="后置任务 ID"
    )
    dependency_type = Column(String(10), default="FS", comment="依赖类型：FS/SS/FF/SF")
    lag_days = Column(Integer, default=0, comment="延迟天数")
    
    # 关系
    schedule = relationship("ProjectDeliverySchedule")
    predecessor = relationship(
        "ProjectDeliveryTask",
        foreign_keys=[predecessor_task_id],
        primaryjoin="ProjectDeliveryDependency.predecessor_task_id==ProjectDeliveryTask.id"
    )
    successor = relationship(
        "ProjectDeliveryTask",
        foreign_keys=[successor_task_id],
        primaryjoin="ProjectDeliveryDependency.successor_task_id==ProjectDeliveryTask.id"
    )
    
    __table_args__ = (
        Index("idx_pdd_schedule", "schedule_id"),
        Index("idx_pdd_predecessor", "predecessor_task_id"),
        Index("idx_pdd_successor", "successor_task_id"),
        UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_dependency"),
    )
    
    def __repr__(self):
        return f"<ProjectDeliveryDependency {self.predecessor_task_id} -> {self.successor_task_id}>"
