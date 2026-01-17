# -*- coding: utf-8 -*-
"""
生产异常模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
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
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='关联项目ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='设备ID')

    # 上报信息
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上报人ID')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='上报时间')

    # 处理信息
    status = Column(String(20), nullable=False, default='REPORTED', comment='状态')
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='处理人ID')
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
