# -*- coding: utf-8 -*-
"""
缺料管理 - 到货跟踪模型
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class MaterialArrival(Base, TimestampMixin):
    """到货跟踪表"""
    __tablename__ = 'material_arrivals'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    arrival_no = Column(String(50), unique=True, nullable=False, comment='到货跟踪单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True, comment='关联采购订单ID')
    purchase_order_item_id = Column(Integer, ForeignKey('purchase_order_items.id'), nullable=True, comment='关联采购订单明细ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    expected_qty = Column(Numeric(10, 4), nullable=False, comment='预期到货数量')

    # 供应商信息
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=True, comment='供应商ID')
    supplier_name = Column(String(200), comment='供应商名称')

    # 时间信息
    expected_date = Column(Date, nullable=False, comment='预期到货日期')
    actual_date = Column(Date, nullable=True, comment='实际到货日期')
    is_delayed = Column(Boolean, default=False, comment='是否延迟')
    delay_days = Column(Integer, default=0, comment='延迟天数')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态：PENDING/IN_TRANSIT/DELAYED/RECEIVED/CANCELLED')
    received_qty = Column(Numeric(10, 4), default=0, comment='实收数量')
    received_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='收货人ID')
    received_at = Column(DateTime, nullable=True, comment='收货时间')

    # 跟催信息
    follow_up_count = Column(Integer, default=0, comment='跟催次数')
    last_follow_up_at = Column(DateTime, nullable=True, comment='最后跟催时间')

    remark = Column(Text, comment='备注')

    # 关系
    shortage_report = relationship('ShortageReport')
    material = relationship('Material')
    # supplier = relationship('Supplier')  # 已禁用 - Supplier 是废弃模型
    follow_ups = relationship('ArrivalFollowUp', back_populates='arrival', lazy='dynamic')

    __table_args__ = (
        Index('idx_arrival_no', 'arrival_no'),
        Index('idx_arrival_status', 'status'),
        Index('idx_arrival_expected_date', 'expected_date'),
        {'comment': '到货跟踪表'}
    )


class ArrivalFollowUp(Base, TimestampMixin):
    """到货跟催记录表"""
    __tablename__ = 'arrival_follow_ups'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    arrival_id = Column(Integer, ForeignKey('material_arrivals.id'), nullable=False, comment='到货跟踪ID')
    follow_up_type = Column(String(20), default='CALL', comment='跟催方式：CALL/EMAIL/VISIT/OTHER')
    follow_up_note = Column(Text, nullable=False, comment='跟催内容')
    followed_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='跟催人ID')
    followed_at = Column(DateTime, nullable=False, default=datetime.now, comment='跟催时间')
    supplier_response = Column(Text, comment='供应商反馈')
    next_follow_up_date = Column(Date, comment='下次跟催日期')

    # 关系
    arrival = relationship('MaterialArrival', back_populates='follow_ups')

    __table_args__ = (
        Index('idx_follow_up_arrival', 'arrival_id'),
        {'comment': '到货跟催记录表'}
    )
