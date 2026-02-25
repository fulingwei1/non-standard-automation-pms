# -*- coding: utf-8 -*-
"""
设备管理模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


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
    """设备保养/维修记录
    
    【状态】未启用 - 设备维护"""
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
