# -*- coding: utf-8 -*-
"""
车间管理模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Workshop(Base, TimestampMixin):
    """车间"""
    __tablename__ = 'workshop'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    workshop_code = Column(String(50), unique=True, nullable=False, comment='车间编码')
    workshop_name = Column(String(100), nullable=False, comment='车间名称')
    workshop_type = Column(String(20), nullable=False, default='OTHER', comment='车间类型')
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='车间主管ID')
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
