# -*- coding: utf-8 -*-
"""
生产管理模块 ORM 模型
包含：车间、工位、生产计划、工单、报工、异常、领料、设备、工序
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, 
    Numeric, ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================

from enum import Enum

class WorkshopTypeEnum(str, Enum):
    """车间类型"""
    MACHINING = 'MACHINING'      # 机加车间
    ASSEMBLY = 'ASSEMBLY'        # 装配车间
    DEBUGGING = 'DEBUGGING'      # 调试车间
    WELDING = 'WELDING'          # 焊接车间
    SURFACE = 'SURFACE'          # 表面处理车间
    WAREHOUSE = 'WAREHOUSE'      # 仓库
    OTHER = 'OTHER'              # 其他


class WorkstationStatusEnum(str, Enum):
    """工位状态"""
    IDLE = 'IDLE'                # 空闲
    WORKING = 'WORKING'          # 工作中
    MAINTENANCE = 'MAINTENANCE'  # 维护中
    DISABLED = 'DISABLED'        # 停用


class WorkerStatusEnum(str, Enum):
    """工人状态"""
    ACTIVE = 'ACTIVE'      # 在岗
    LEAVE = 'LEAVE'        # 请假
    RESIGNED = 'RESIGNED'  # 离职


class SkillLevelEnum(str, Enum):
    """技能等级"""
    JUNIOR = 'JUNIOR'          # 初级
    INTERMEDIATE = 'INTERMEDIATE'  # 中级
    SENIOR = 'SENIOR'          # 高级
    EXPERT = 'EXPERT'          # 专家


class ProductionPlanTypeEnum(str, Enum):
    """生产计划类型"""
    MASTER = 'MASTER'        # 主生产计划(MPS)
    WORKSHOP = 'WORKSHOP'    # 车间作业计划


class ProductionPlanStatusEnum(str, Enum):
    """生产计划状态"""
    DRAFT = 'DRAFT'              # 草稿
    SUBMITTED = 'SUBMITTED'      # 已提交
    APPROVED = 'APPROVED'        # 已审批
    PUBLISHED = 'PUBLISHED'      # 已发布
    EXECUTING = 'EXECUTING'      # 执行中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class WorkOrderTypeEnum(str, Enum):
    """工单类型"""
    MACHINING = 'MACHINING'    # 机加
    ASSEMBLY = 'ASSEMBLY'      # 装配
    DEBUGGING = 'DEBUGGING'    # 调试
    WELDING = 'WELDING'        # 焊接
    INSPECTION = 'INSPECTION'  # 检验
    OTHER = 'OTHER'            # 其他


class WorkOrderStatusEnum(str, Enum):
    """工单状态"""
    PENDING = 'PENDING'          # 待派工
    ASSIGNED = 'ASSIGNED'        # 已派工
    STARTED = 'STARTED'          # 已开工
    PAUSED = 'PAUSED'            # 已暂停
    COMPLETED = 'COMPLETED'      # 已完工
    APPROVED = 'APPROVED'        # 已审核
    CANCELLED = 'CANCELLED'      # 已取消


class WorkOrderPriorityEnum(str, Enum):
    """工单优先级"""
    LOW = 'LOW'          # 低
    NORMAL = 'NORMAL'    # 普通
    HIGH = 'HIGH'        # 高
    URGENT = 'URGENT'    # 紧急


class WorkReportTypeEnum(str, Enum):
    """报工类型"""
    START = 'START'          # 开工
    PROGRESS = 'PROGRESS'    # 进度
    PAUSE = 'PAUSE'          # 暂停
    RESUME = 'RESUME'        # 恢复
    COMPLETE = 'COMPLETE'    # 完工


class WorkReportStatusEnum(str, Enum):
    """报工状态"""
    PENDING = 'PENDING'      # 待审核
    APPROVED = 'APPROVED'    # 已通过
    REJECTED = 'REJECTED'    # 已驳回


class ProductionExceptionTypeEnum(str, Enum):
    """生产异常类型"""
    MATERIAL = 'MATERIAL'      # 物料异常
    EQUIPMENT = 'EQUIPMENT'    # 设备异常
    QUALITY = 'QUALITY'        # 质量异常
    PROCESS = 'PROCESS'        # 工艺异常
    SAFETY = 'SAFETY'          # 安全异常
    OTHER = 'OTHER'            # 其他


class ProductionExceptionLevelEnum(str, Enum):
    """生产异常级别"""
    MINOR = 'MINOR'        # 轻微
    MAJOR = 'MAJOR'        # 一般
    CRITICAL = 'CRITICAL'  # 严重


class ProductionExceptionStatusEnum(str, Enum):
    """生产异常状态"""
    REPORTED = 'REPORTED'    # 已上报
    HANDLING = 'HANDLING'    # 处理中
    RESOLVED = 'RESOLVED'    # 已解决
    CLOSED = 'CLOSED'        # 已关闭


class MaterialRequisitionStatusEnum(str, Enum):
    """领料单状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    APPROVED = 'APPROVED'    # 已审批
    REJECTED = 'REJECTED'    # 已驳回
    ISSUED = 'ISSUED'        # 已发料
    COMPLETED = 'COMPLETED'  # 已完成
    CANCELLED = 'CANCELLED'  # 已取消


class EquipmentStatusEnum(str, Enum):
    """设备状态"""
    IDLE = 'IDLE'                # 空闲
    RUNNING = 'RUNNING'          # 运行中
    MAINTENANCE = 'MAINTENANCE'  # 保养中
    REPAIR = 'REPAIR'            # 维修中
    DISABLED = 'DISABLED'        # 停用


class ProcessTypeEnum(str, Enum):
    """工序类型"""
    MACHINING = 'MACHINING'    # 机加
    ASSEMBLY = 'ASSEMBLY'      # 装配
    DEBUGGING = 'DEBUGGING'    # 调试
    WELDING = 'WELDING'        # 焊接
    SURFACE = 'SURFACE'        # 表面处理
    INSPECTION = 'INSPECTION'  # 检验
    OTHER = 'OTHER'            # 其他


# ==================== 车间管理 ====================

class Workshop(Base, TimestampMixin):
    """车间"""
    __tablename__ = 'workshop'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    workshop_code = Column(String(50), unique=True, nullable=False, comment='车间编码')
    workshop_name = Column(String(100), nullable=False, comment='车间名称')
    workshop_type = Column(String(20), nullable=False, default='OTHER', comment='车间类型')
    manager_id = Column(Integer, ForeignKey('user.id'), nullable=True, comment='车间主管ID')
    location = Column(String(200), nullable=True, comment='车间位置')
    capacity_hours = Column(Numeric(10, 2), nullable=True, comment='日产能(工时)')
    description = Column(Text, nullable=True, comment='描述')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    
    # 关系
    workstations = relationship('Workstation', back_populates='workshop')
    workers = relationship('Worker', back_populates='workshop')
    work_orders = relationship('WorkOrder', back_populates='workshop')
    
    __table_args__ = (
        Index('idx_workshop_code', 'workshop_code'),
        Index('idx_workshop_type', 'workshop_type'),
        {'comment': '车间表'}
    )


class Workstation(Base, TimestampMixin):
    """工位"""
    __tablename__ = 'workstation'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    workstation_code = Column(String(50), unique=True, nullable=False, comment='工位编码')
    workstation_name = Column(String(100), nullable=False, comment='工位名称')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=False, comment='所属车间ID')
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='关联设备ID')
    status = Column(String(20), nullable=False, default='IDLE', comment='工位状态')
    current_worker_id = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='当前操作工ID')
    current_work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='当前工单ID')
    description = Column(Text, nullable=True, comment='描述')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    
    # 关系
    workshop = relationship('Workshop', back_populates='workstations')
    equipment = relationship('Equipment', back_populates='workstation')
    
    __table_args__ = (
        Index('idx_workstation_code', 'workstation_code'),
        Index('idx_workstation_workshop', 'workshop_id'),
        Index('idx_workstation_status', 'status'),
        {'comment': '工位表'}
    )


# ==================== 人员管理 ====================

class Worker(Base, TimestampMixin):
    """生产人员"""
    __tablename__ = 'worker'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    worker_no = Column(String(50), unique=True, nullable=False, comment='工号')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, comment='关联用户ID')
    worker_name = Column(String(50), nullable=False, comment='姓名')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='所属车间ID')
    position = Column(String(50), nullable=True, comment='岗位')
    skill_level = Column(String(20), nullable=True, default='JUNIOR', comment='技能等级')
    phone = Column(String(20), nullable=True, comment='联系电话')
    entry_date = Column(Date, nullable=True, comment='入职日期')
    status = Column(String(20), nullable=False, default='ACTIVE', comment='状态')
    hourly_rate = Column(Numeric(10, 2), nullable=True, comment='时薪(元)')
    remark = Column(Text, nullable=True, comment='备注')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否在职')
    
    # 关系
    workshop = relationship('Workshop', back_populates='workers')
    skills = relationship('WorkerSkill', back_populates='worker')
    work_orders = relationship('WorkOrder', back_populates='assigned_worker', foreign_keys='WorkOrder.assigned_to')
    work_reports = relationship('WorkReport', back_populates='worker')
    
    __table_args__ = (
        Index('idx_worker_no', 'worker_no'),
        Index('idx_worker_workshop', 'workshop_id'),
        Index('idx_worker_status', 'status'),
        {'comment': '生产人员表'}
    )


class WorkerSkill(Base, TimestampMixin):
    """工人技能"""
    __tablename__ = 'worker_skill'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False, comment='工人ID')
    process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=False, comment='工序ID')
    skill_level = Column(String(20), nullable=False, default='JUNIOR', comment='技能等级')
    certified_date = Column(Date, nullable=True, comment='认证日期')
    expiry_date = Column(Date, nullable=True, comment='有效期')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    worker = relationship('Worker', back_populates='skills')
    process = relationship('ProcessDict', back_populates='worker_skills')
    
    __table_args__ = (
        Index('idx_worker_skill_worker', 'worker_id'),
        Index('idx_worker_skill_process', 'process_id'),
        {'comment': '工人技能表'}
    )


# ==================== 工序字典 ====================

class ProcessDict(Base, TimestampMixin):
    """工序字典"""
    __tablename__ = 'process_dict'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    process_code = Column(String(50), unique=True, nullable=False, comment='工序编码')
    process_name = Column(String(100), nullable=False, comment='工序名称')
    process_type = Column(String(20), nullable=False, default='OTHER', comment='工序类型')
    standard_hours = Column(Numeric(10, 2), nullable=True, comment='标准工时(小时)')
    description = Column(Text, nullable=True, comment='描述')
    work_instruction = Column(Text, nullable=True, comment='作业指导')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    
    # 关系
    worker_skills = relationship('WorkerSkill', back_populates='process')
    work_orders = relationship('WorkOrder', back_populates='process')
    
    __table_args__ = (
        Index('idx_process_code', 'process_code'),
        Index('idx_process_type', 'process_type'),
        {'comment': '工序字典表'}
    )


# ==================== 设备管理 ====================

class Equipment(Base, TimestampMixin):
    """设备"""
    __tablename__ = 'equipment'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    equipment_code = Column(String(50), unique=True, nullable=False, comment='设备编码')
    equipment_name = Column(String(100), nullable=False, comment='设备名称')
    model = Column(String(100), nullable=True, comment='型号规格')
    manufacturer = Column(String(100), nullable=True, comment='生产厂家')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='所属车间ID')
    purchase_date = Column(Date, nullable=True, comment='购置日期')
    status = Column(String(20), nullable=False, default='IDLE', comment='设备状态')
    last_maintenance_date = Column(Date, nullable=True, comment='上次保养日期')
    next_maintenance_date = Column(Date, nullable=True, comment='下次保养日期')
    asset_no = Column(String(50), nullable=True, comment='固定资产编号')
    remark = Column(Text, nullable=True, comment='备注')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    
    # 关系
    workstation = relationship('Workstation', back_populates='equipment', uselist=False)
    maintenance_records = relationship('EquipmentMaintenance', back_populates='equipment')
    
    __table_args__ = (
        Index('idx_equipment_code', 'equipment_code'),
        Index('idx_equipment_workshop', 'workshop_id'),
        Index('idx_equipment_status', 'status'),
        {'comment': '设备表'}
    )


class EquipmentMaintenance(Base, TimestampMixin):
    """设备保养/维修记录"""
    __tablename__ = 'equipment_maintenance'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=False, comment='设备ID')
    maintenance_type = Column(String(20), nullable=False, comment='类型:maintenance/repair')
    maintenance_date = Column(Date, nullable=False, comment='保养/维修日期')
    content = Column(Text, nullable=True, comment='保养/维修内容')
    cost = Column(Numeric(14, 2), nullable=True, comment='费用')
    performed_by = Column(String(50), nullable=True, comment='执行人')
    next_maintenance_date = Column(Date, nullable=True, comment='下次保养日期')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    equipment = relationship('Equipment', back_populates='maintenance_records')
    
    __table_args__ = (
        Index('idx_equip_maint_equipment', 'equipment_id'),
        Index('idx_equip_maint_date', 'maintenance_date'),
        {'comment': '设备保养维修记录表'}
    )


# ==================== 生产计划 ====================

class ProductionPlan(Base, TimestampMixin):
    """生产计划"""
    __tablename__ = 'production_plan'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    plan_no = Column(String(50), unique=True, nullable=False, comment='计划编号')
    plan_name = Column(String(200), nullable=False, comment='计划名称')
    plan_type = Column(String(20), nullable=False, default='MASTER', comment='计划类型:MASTER/WORKSHOP')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, comment='关联项目ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID(车间计划)')
    plan_start_date = Column(Date, nullable=False, comment='计划开始日期')
    plan_end_date = Column(Date, nullable=False, comment='计划结束日期')
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态')
    progress = Column(Integer, default=0, comment='进度(%)')
    description = Column(Text, nullable=True, comment='计划说明')
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='创建人ID')
    approved_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    work_orders = relationship('WorkOrder', back_populates='production_plan')
    
    __table_args__ = (
        Index('idx_prod_plan_no', 'plan_no'),
        Index('idx_prod_plan_project', 'project_id'),
        Index('idx_prod_plan_workshop', 'workshop_id'),
        Index('idx_prod_plan_status', 'status'),
        Index('idx_prod_plan_dates', 'plan_start_date', 'plan_end_date'),
        {'comment': '生产计划表'}
    )


# ==================== 生产工单 ====================

class WorkOrder(Base, TimestampMixin):
    """生产工单"""
    __tablename__ = 'work_order'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_order_no = Column(String(50), unique=True, nullable=False, comment='工单编号')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(20), nullable=False, default='OTHER', comment='工单类型')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machine.id'), nullable=True, comment='机台ID')
    production_plan_id = Column(Integer, ForeignKey('production_plan.id'), nullable=True, comment='生产计划ID')
    process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=True, comment='工序ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')
    
    # 物料相关
    material_id = Column(Integer, ForeignKey('material.id'), nullable=True, comment='物料ID')
    material_name = Column(String(200), nullable=True, comment='物料名称')
    specification = Column(String(200), nullable=True, comment='规格型号')
    drawing_no = Column(String(100), nullable=True, comment='图纸编号')
    
    # 计划信息
    plan_qty = Column(Integer, default=1, comment='计划数量')
    completed_qty = Column(Integer, default=0, comment='完成数量')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    defect_qty = Column(Integer, default=0, comment='不良数量')
    standard_hours = Column(Numeric(10, 2), nullable=True, comment='标准工时(小时)')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时(小时)')
    
    # 时间安排
    plan_start_date = Column(Date, nullable=True, comment='计划开始日期')
    plan_end_date = Column(Date, nullable=True, comment='计划结束日期')
    actual_start_time = Column(DateTime, nullable=True, comment='实际开始时间')
    actual_end_time = Column(DateTime, nullable=True, comment='实际结束时间')
    
    # 派工信息
    assigned_to = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='指派给(工人ID)')
    assigned_at = Column(DateTime, nullable=True, comment='派工时间')
    assigned_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='派工人ID')
    
    # 状态信息
    status = Column(String(20), nullable=False, default='PENDING', comment='状态')
    priority = Column(String(20), nullable=False, default='NORMAL', comment='优先级')
    progress = Column(Integer, default=0, comment='进度(%)')
    
    # 其他
    work_content = Column(Text, nullable=True, comment='工作内容')
    remark = Column(Text, nullable=True, comment='备注')
    pause_reason = Column(Text, nullable=True, comment='暂停原因')
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='创建人ID')
    
    # 关系
    production_plan = relationship('ProductionPlan', back_populates='work_orders')
    workshop = relationship('Workshop', back_populates='work_orders')
    process = relationship('ProcessDict', back_populates='work_orders')
    assigned_worker = relationship('Worker', back_populates='work_orders', foreign_keys=[assigned_to])
    work_reports = relationship('WorkReport', back_populates='work_order')
    material_requisitions = relationship('MaterialRequisition', back_populates='work_order')
    exceptions = relationship('ProductionException', back_populates='work_order')
    
    __table_args__ = (
        Index('idx_work_order_no', 'work_order_no'),
        Index('idx_work_order_project', 'project_id'),
        Index('idx_work_order_plan', 'production_plan_id'),
        Index('idx_work_order_workshop', 'workshop_id'),
        Index('idx_work_order_assigned', 'assigned_to'),
        Index('idx_work_order_status', 'status'),
        Index('idx_work_order_priority', 'priority'),
        Index('idx_work_order_dates', 'plan_start_date', 'plan_end_date'),
        {'comment': '生产工单表'}
    )


# ==================== 报工管理 ====================

class WorkReport(Base, TimestampMixin):
    """报工记录"""
    __tablename__ = 'work_report'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='报工单号')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False, comment='工人ID')
    report_type = Column(String(20), nullable=False, comment='报工类型:START/PROGRESS/PAUSE/RESUME/COMPLETE')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='报工时间')
    
    # 进度信息
    progress_percent = Column(Integer, nullable=True, comment='进度百分比')
    work_hours = Column(Numeric(10, 2), nullable=True, comment='本次工时(小时)')
    
    # 完工信息
    completed_qty = Column(Integer, nullable=True, comment='完成数量')
    qualified_qty = Column(Integer, nullable=True, comment='合格数量')
    defect_qty = Column(Integer, nullable=True, comment='不良数量')
    
    # 审核信息
    status = Column(String(20), nullable=False, default='PENDING', comment='状态')
    approved_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='审核人ID')
    approved_at = Column(DateTime, nullable=True, comment='审核时间')
    approve_comment = Column(Text, nullable=True, comment='审核意见')
    
    # 其他
    description = Column(Text, nullable=True, comment='工作描述')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    work_order = relationship('WorkOrder', back_populates='work_reports')
    worker = relationship('Worker', back_populates='work_reports')
    
    __table_args__ = (
        Index('idx_work_report_no', 'report_no'),
        Index('idx_work_report_order', 'work_order_id'),
        Index('idx_work_report_worker', 'worker_id'),
        Index('idx_work_report_type', 'report_type'),
        Index('idx_work_report_status', 'status'),
        Index('idx_work_report_time', 'report_time'),
        {'comment': '报工记录表'}
    )


# ==================== 生产异常 ====================

class ProductionException(Base, TimestampMixin):
    """生产异常"""
    __tablename__ = 'production_exception'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    exception_no = Column(String(50), unique=True, nullable=False, comment='异常编号')
    exception_type = Column(String(20), nullable=False, comment='异常类型')
    exception_level = Column(String(20), nullable=False, default='MINOR', comment='异常级别')
    title = Column(String(200), nullable=False, comment='异常标题')
    description = Column(Text, nullable=True, comment='异常描述')
    
    # 关联信息
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='关联工单ID')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, comment='关联项目ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='设备ID')
    
    # 上报信息
    reporter_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='上报人ID')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='上报时间')
    
    # 处理信息
    status = Column(String(20), nullable=False, default='REPORTED', comment='状态')
    handler_id = Column(Integer, ForeignKey('user.id'), nullable=True, comment='处理人ID')
    handle_plan = Column(Text, nullable=True, comment='处理方案')
    handle_result = Column(Text, nullable=True, comment='处理结果')
    handle_time = Column(DateTime, nullable=True, comment='处理时间')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')
    
    # 影响评估
    impact_hours = Column(Numeric(10, 2), nullable=True, comment='影响工时(小时)')
    impact_cost = Column(Numeric(14, 2), nullable=True, comment='影响成本(元)')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    work_order = relationship('WorkOrder', back_populates='exceptions')
    
    __table_args__ = (
        Index('idx_prod_exc_no', 'exception_no'),
        Index('idx_prod_exc_type', 'exception_type'),
        Index('idx_prod_exc_level', 'exception_level'),
        Index('idx_prod_exc_status', 'status'),
        Index('idx_prod_exc_work_order', 'work_order_id'),
        Index('idx_prod_exc_project', 'project_id'),
        {'comment': '生产异常表'}
    )


# ==================== 领料管理 ====================

class MaterialRequisition(Base, TimestampMixin):
    """领料单"""
    __tablename__ = 'material_requisition'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requisition_no = Column(String(50), unique=True, nullable=False, comment='领料单号')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='关联工单ID')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, comment='项目ID')
    
    # 申请信息
    applicant_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='申请人ID')
    apply_time = Column(DateTime, nullable=False, default=datetime.now, comment='申请时间')
    apply_reason = Column(Text, nullable=True, comment='申请原因')
    
    # 审批信息
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态')
    approved_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approve_comment = Column(Text, nullable=True, comment='审批意见')
    
    # 发料信息
    issued_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='发料人ID')
    issued_at = Column(DateTime, nullable=True, comment='发料时间')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    work_order = relationship('WorkOrder', back_populates='material_requisitions')
    items = relationship('MaterialRequisitionItem', back_populates='requisition')
    
    __table_args__ = (
        Index('idx_mat_req_no', 'requisition_no'),
        Index('idx_mat_req_work_order', 'work_order_id'),
        Index('idx_mat_req_project', 'project_id'),
        Index('idx_mat_req_status', 'status'),
        {'comment': '领料单表'}
    )


class MaterialRequisitionItem(Base, TimestampMixin):
    """领料单明细"""
    __tablename__ = 'material_requisition_item'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requisition_id = Column(Integer, ForeignKey('material_requisition.id'), nullable=False, comment='领料单ID')
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False, comment='物料ID')
    
    request_qty = Column(Numeric(14, 4), nullable=False, comment='申请数量')
    approved_qty = Column(Numeric(14, 4), nullable=True, comment='批准数量')
    issued_qty = Column(Numeric(14, 4), nullable=True, comment='发放数量')
    unit = Column(String(20), nullable=True, comment='单位')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    requisition = relationship('MaterialRequisition', back_populates='items')
    
    __table_args__ = (
        Index('idx_mat_req_item_requisition', 'requisition_id'),
        Index('idx_mat_req_item_material', 'material_id'),
        {'comment': '领料单明细表'}
    )


# ==================== 生产日报 ====================

class ProductionDailyReport(Base, TimestampMixin):
    """生产日报"""
    __tablename__ = 'production_daily_report'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_date = Column(Date, nullable=False, comment='报告日期')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID(空表示全厂)')
    
    # 生产统计
    plan_qty = Column(Integer, default=0, comment='计划数量')
    completed_qty = Column(Integer, default=0, comment='完成数量')
    completion_rate = Column(Numeric(5, 2), default=0, comment='完成率(%)')
    
    # 工时统计
    plan_hours = Column(Numeric(10, 2), default=0, comment='计划工时')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时')
    overtime_hours = Column(Numeric(10, 2), default=0, comment='加班工时')
    efficiency = Column(Numeric(5, 2), default=0, comment='效率(%)')
    
    # 出勤统计
    should_attend = Column(Integer, default=0, comment='应出勤人数')
    actual_attend = Column(Integer, default=0, comment='实际出勤')
    leave_count = Column(Integer, default=0, comment='请假人数')
    
    # 质量统计
    total_qty = Column(Integer, default=0, comment='生产总数')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    pass_rate = Column(Numeric(5, 2), default=0, comment='合格率(%)')
    
    # 异常统计
    new_exception_count = Column(Integer, default=0, comment='新增异常数')
    resolved_exception_count = Column(Integer, default=0, comment='解决异常数')
    
    summary = Column(Text, nullable=True, comment='日报总结')
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True, comment='创建人ID')
    
    __table_args__ = (
        Index('idx_prod_daily_date', 'report_date'),
        Index('idx_prod_daily_workshop', 'workshop_id'),
        Index('idx_prod_daily_date_workshop', 'report_date', 'workshop_id', unique=True),
        {'comment': '生产日报表'}
    )

