# -*- coding: utf-8 -*-
"""
生产工单模型
"""
from sqlalchemy import (
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

from app.models.base import Base, TimestampMixin


class WorkOrder(Base, TimestampMixin):
    """生产工单"""
    __tablename__ = 'work_order'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_order_no = Column(String(50), unique=True, nullable=False, comment='工单编号')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(20), nullable=False, default='OTHER', comment='工单类型')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=True, comment='机台ID')
    production_plan_id = Column(Integer, ForeignKey('production_plan.id'), nullable=True, comment='生产计划ID')
    process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=True, comment='工序ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')

    # 物料相关
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
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
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='派工人ID')

    # 状态信息
    status = Column(String(20), nullable=False, default='PENDING', comment='状态')
    priority = Column(String(20), nullable=False, default='NORMAL', comment='优先级')
    progress = Column(Integer, default=0, comment='进度(%)')

    # 其他
    work_content = Column(Text, nullable=True, comment='工作内容')
    remark = Column(Text, nullable=True, comment='备注')
    pause_reason = Column(Text, nullable=True, comment='暂停原因')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

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
