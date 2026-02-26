# -*- coding: utf-8 -*-
"""
仓储管理模块模型
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Warehouse(Base, TimestampMixin):
    """仓库表"""
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_code = Column(String(50), unique=True, nullable=False, comment='仓库编码')
    warehouse_name = Column(String(200), nullable=False, comment='仓库名称')
    warehouse_type = Column(String(50), default='NORMAL', comment='仓库类型: NORMAL/TEMPORARY/VIRTUAL')
    address = Column(String(500), comment='地址')
    manager = Column(String(100), comment='负责人')
    contact_phone = Column(String(50), comment='联系电话')
    capacity = Column(Numeric(12, 2), comment='容量')
    description = Column(Text, comment='描述')
    is_active = Column(Boolean, default=True, comment='是否启用')

    locations = relationship('WarehouseLocation', back_populates='warehouse')

    def __repr__(self):
        return f'<Warehouse {self.warehouse_code}>'


class WarehouseLocation(Base, TimestampMixin):
    """库位表"""
    __tablename__ = 'warehouse_locations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False, comment='仓库ID')
    location_code = Column(String(50), nullable=False, comment='库位编码')
    location_name = Column(String(200), comment='库位名称')
    zone = Column(String(50), comment='区域: A/B/C...')
    aisle = Column(String(20), comment='通道')
    shelf = Column(String(20), comment='货架')
    level = Column(String(20), comment='层')
    position = Column(String(20), comment='位')
    capacity = Column(Numeric(12, 2), comment='容量')
    location_type = Column(String(50), default='STORAGE', comment='类型: STORAGE/PICKING/STAGING/RETURN')
    is_active = Column(Boolean, default=True, comment='是否启用')

    warehouse = relationship('Warehouse', back_populates='locations')

    __table_args__ = (
        Index('ix_warehouse_location_code', 'warehouse_id', 'location_code', unique=True),
    )

    def __repr__(self):
        return f'<WarehouseLocation {self.location_code}>'


class InboundOrder(Base, TimestampMixin):
    """入库单"""
    __tablename__ = 'inbound_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='入库单号')
    order_type = Column(String(50), default='PURCHASE', comment='入库类型: PURCHASE/RETURN/TRANSFER/OTHER')
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), comment='目标仓库ID')
    source_no = Column(String(50), comment='来源单号(采购单号等)')
    supplier_name = Column(String(200), comment='供应商名称')
    status = Column(String(20), default='DRAFT', comment='状态: DRAFT/PENDING/RECEIVING/COMPLETED/CANCELLED')
    planned_date = Column(Date, comment='计划入库日期')
    actual_date = Column(Date, comment='实际入库日期')
    operator = Column(String(100), comment='操作员')
    remark = Column(Text, comment='备注')
    total_quantity = Column(Numeric(12, 2), default=0, comment='总数量')
    received_quantity = Column(Numeric(12, 2), default=0, comment='已收数量')
    created_by = Column(Integer, comment='创建人ID')

    items = relationship('InboundOrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<InboundOrder {self.order_no}>'


class InboundOrderItem(Base, TimestampMixin):
    """入库单明细"""
    __tablename__ = 'inbound_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('inbound_orders.id'), nullable=False, comment='入库单ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')
    planned_quantity = Column(Numeric(12, 2), nullable=False, comment='计划数量')
    received_quantity = Column(Numeric(12, 2), default=0, comment='实收数量')
    location_id = Column(Integer, ForeignKey('warehouse_locations.id'), comment='目标库位ID')
    remark = Column(Text, comment='备注')

    order = relationship('InboundOrder', back_populates='items')


class OutboundOrder(Base, TimestampMixin):
    """出库单"""
    __tablename__ = 'outbound_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='出库单号')
    order_type = Column(String(50), default='PRODUCTION', comment='出库类型: PRODUCTION/SALES/TRANSFER/SCRAP/OTHER')
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), comment='来源仓库ID')
    target_no = Column(String(50), comment='目标单号(工单号等)')
    department = Column(String(200), comment='领料部门')
    status = Column(String(20), default='DRAFT', comment='状态: DRAFT/PENDING/PICKING/COMPLETED/CANCELLED')
    planned_date = Column(Date, comment='计划出库日期')
    actual_date = Column(Date, comment='实际出库日期')
    operator = Column(String(100), comment='操作员')
    remark = Column(Text, comment='备注')
    total_quantity = Column(Numeric(12, 2), default=0, comment='总数量')
    picked_quantity = Column(Numeric(12, 2), default=0, comment='已拣数量')
    created_by = Column(Integer, comment='创建人ID')
    is_urgent = Column(Boolean, default=False, comment='是否紧急')

    items = relationship('OutboundOrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<OutboundOrder {self.order_no}>'


class OutboundOrderItem(Base, TimestampMixin):
    """出库单明细"""
    __tablename__ = 'outbound_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('outbound_orders.id'), nullable=False, comment='出库单ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')
    planned_quantity = Column(Numeric(12, 2), nullable=False, comment='计划数量')
    picked_quantity = Column(Numeric(12, 2), default=0, comment='实拣数量')
    location_id = Column(Integer, ForeignKey('warehouse_locations.id'), comment='来源库位ID')
    remark = Column(Text, comment='备注')

    order = relationship('OutboundOrder', back_populates='items')


class Inventory(Base, TimestampMixin):
    """库存表"""
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False, comment='仓库ID')
    location_id = Column(Integer, ForeignKey('warehouse_locations.id'), comment='库位ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')
    quantity = Column(Numeric(12, 2), default=0, comment='库存数量')
    reserved_quantity = Column(Numeric(12, 2), default=0, comment='预留数量')
    available_quantity = Column(Numeric(12, 2), default=0, comment='可用数量')
    min_stock = Column(Numeric(12, 2), default=0, comment='最低库存')
    max_stock = Column(Numeric(12, 2), default=0, comment='最高库存')
    batch_no = Column(String(100), comment='批次号')
    last_inbound_date = Column(DateTime, comment='最后入库时间')
    last_outbound_date = Column(DateTime, comment='最后出库时间')

    __table_args__ = (
        Index('ix_inventory_material', 'warehouse_id', 'material_code', 'batch_no'),
    )

    def __repr__(self):
        return f'<Inventory {self.material_code} qty={self.quantity}>'


class StockCountOrder(Base, TimestampMixin):
    """盘点单"""
    __tablename__ = 'stock_count_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    count_no = Column(String(50), unique=True, nullable=False, comment='盘点单号')
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), comment='仓库ID')
    count_type = Column(String(50), default='FULL', comment='盘点类型: FULL/PARTIAL/CYCLE')
    status = Column(String(20), default='DRAFT', comment='状态: DRAFT/IN_PROGRESS/COMPLETED/CANCELLED')
    planned_date = Column(Date, comment='计划盘点日期')
    actual_date = Column(Date, comment='实际盘点日期')
    operator = Column(String(100), comment='盘点员')
    remark = Column(Text, comment='备注')
    total_items = Column(Integer, default=0, comment='盘点项数')
    matched_items = Column(Integer, default=0, comment='一致项数')
    diff_items = Column(Integer, default=0, comment='差异项数')
    created_by = Column(Integer, comment='创建人ID')

    items = relationship('StockCountItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<StockCountOrder {self.count_no}>'


class StockCountItem(Base, TimestampMixin):
    """盘点明细"""
    __tablename__ = 'stock_count_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('stock_count_orders.id'), nullable=False, comment='盘点单ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), comment='物料名称')
    location_id = Column(Integer, ForeignKey('warehouse_locations.id'), comment='库位ID')
    system_quantity = Column(Numeric(12, 2), default=0, comment='系统数量')
    actual_quantity = Column(Numeric(12, 2), comment='实盘数量')
    diff_quantity = Column(Numeric(12, 2), comment='差异数量')
    diff_reason = Column(Text, comment='差异原因')

    order = relationship('StockCountOrder', back_populates='items')
