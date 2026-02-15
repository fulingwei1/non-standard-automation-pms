# -*- coding: utf-8 -*-
"""
设备OEE记录模型
OEE (Overall Equipment Effectiveness) = 可用率 × 性能率 × 合格率
"""
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
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class EquipmentOEERecord(Base, TimestampMixin):
    """设备OEE记录表"""
    __tablename__ = 'equipment_oee_record'
    __table_args__ = (
        Index('idx_oee_equipment_date', 'equipment_id', 'record_date'),
        Index('idx_oee_workshop', 'workshop_id'),
        Index('idx_oee_date', 'record_date'),
        {'extend_existing': True, 'comment': '设备OEE记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联信息
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=False, comment='设备ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')
    
    # 时间信息
    record_date = Column(Date, nullable=False, comment='记录日期')
    shift = Column(String(20), nullable=True, comment='班次(早班/中班/晚班)')
    
    # 时间数据 (分钟)
    planned_production_time = Column(Integer, nullable=False, comment='计划生产时间(分钟)')
    planned_downtime = Column(Integer, default=0, comment='计划停机时间(分钟,如保养)')
    unplanned_downtime = Column(Integer, default=0, comment='非计划停机时间(分钟,如故障)')
    operating_time = Column(Integer, nullable=False, comment='运行时间(分钟) = 计划生产时间 - 停机时间')
    
    # 产量数据
    ideal_cycle_time = Column(Numeric(10, 4), nullable=False, comment='理想单件周期时间(分钟)')
    actual_output = Column(Integer, nullable=False, comment='实际产量(件)')
    target_output = Column(Integer, nullable=False, comment='目标产量(件)')
    
    # 质量数据
    qualified_qty = Column(Integer, nullable=False, comment='合格数量(件)')
    defect_qty = Column(Integer, default=0, comment='不良品数量(件)')
    rework_qty = Column(Integer, default=0, comment='返工数量(件)')
    
    # OEE核心指标 (百分比 0-100)
    availability = Column(Numeric(5, 2), nullable=False, comment='可用率(%) = 运行时间/计划生产时间')
    performance = Column(Numeric(5, 2), nullable=False, comment='性能率(%) = (理想周期×实际产量)/运行时间')
    quality = Column(Numeric(5, 2), nullable=False, comment='合格率(%) = 合格数/实际产量')
    oee = Column(Numeric(5, 2), nullable=False, comment='OEE(%) = 可用率 × 性能率 × 合格率')
    
    # 损失分析 (分钟)
    availability_loss = Column(Integer, default=0, comment='可用性损失(分钟) = 停机时间')
    performance_loss = Column(Integer, default=0, comment='性能损失(分钟) = 理想时间 - 运行时间')
    quality_loss = Column(Integer, default=0, comment='质量损失(分钟) = (不良品/理想周期)')
    
    # 辅助信息
    operator_id = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='操作员ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    downtime_reason = Column(Text, nullable=True, comment='停机原因')
    performance_note = Column(Text, nullable=True, comment='性能备注')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 计算标志
    is_auto_calculated = Column(Boolean, default=False, comment='是否自动计算')
    calculated_at = Column(DateTime, nullable=True, comment='计算时间')
    calculated_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='计算人ID')
    
    # 关系
    equipment = relationship('Equipment', backref='oee_records')
    workshop = relationship('Workshop', backref='oee_records')
    workstation = relationship('Workstation', backref='oee_records')
    operator = relationship('Worker', foreign_keys=[operator_id], backref='operated_oee_records')
    work_order = relationship('WorkOrder', backref='oee_records')
