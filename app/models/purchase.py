# -*- coding: utf-8 -*-
"""
采购管理模块模型
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

from .base import Base, TimestampMixin


class PurchaseOrder(Base, TimestampMixin):
    """采购订单表"""
    __tablename__ = 'purchase_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='订单编号')
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='供应商ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    source_request_id = Column(Integer, ForeignKey('purchase_requests.id'), comment='来源采购申请ID')

    # 订单信息
    order_type = Column(String(20), default='NORMAL', comment='订单类型')
    order_title = Column(String(200), comment='订单标题')

    # 金额
    total_amount = Column(Numeric(14, 2), default=0, comment='总金额')
    tax_rate = Column(Numeric(5, 2), default=13, comment='税率(%)')
    tax_amount = Column(Numeric(14, 2), default=0, comment='税额')
    amount_with_tax = Column(Numeric(14, 2), default=0, comment='含税金额')
    currency = Column(String(10), default='CNY', comment='币种')

    # 时间
    order_date = Column(Date, comment='订单日期')
    required_date = Column(Date, comment='要求交期')
    promised_date = Column(Date, comment='承诺交期')

    # 状态
    status = Column(String(20), default='DRAFT', comment='订单状态')

    # 付款
    payment_terms = Column(String(100), comment='付款条款')
    payment_status = Column(String(20), default='UNPAID', comment='付款状态')
    paid_amount = Column(Numeric(14, 2), default=0, comment='已付金额')

    # 收货
    delivery_address = Column(String(500), comment='收货地址')
    received_amount = Column(Numeric(14, 2), default=0, comment='已收货金额')

    # 审批
    submitted_at = Column(DateTime, comment='提交时间')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')
    approval_note = Column(Text, comment='审批意见')

    # 合同
    contract_no = Column(String(100), comment='合同编号')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    vendor = relationship('Vendor', back_populates='purchase_orders')
    project = relationship('Project')
    source_request = relationship('PurchaseRequest', back_populates='orders')
    items = relationship('PurchaseOrderItem', back_populates='order', lazy='dynamic')
    receipts = relationship('GoodsReceipt', back_populates='order', lazy='dynamic')

    __table_args__ = (
        Index('idx_po_supplier', 'supplier_id'),
        Index('idx_po_project', 'project_id'),
        Index('idx_po_status', 'status'),
        Index('idx_po_source_request', 'source_request_id'),
    )

    def __repr__(self):
        return f'<PurchaseOrder {self.order_no}>'


class PurchaseOrderItem(Base, TimestampMixin):
    """采购订单明细表"""
    __tablename__ = 'purchase_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False, comment='订单ID')
    item_no = Column(Integer, nullable=False, comment='行号')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='BOM行ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')

    # 数量与价格
    quantity = Column(Numeric(10, 4), nullable=False, comment='订购数量')
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    amount = Column(Numeric(14, 2), default=0, comment='金额')
    tax_rate = Column(Numeric(5, 2), default=13, comment='税率')
    tax_amount = Column(Numeric(14, 2), default=0, comment='税额')
    amount_with_tax = Column(Numeric(14, 2), default=0, comment='含税金额')

    # 交期
    required_date = Column(Date, comment='要求交期')
    promised_date = Column(Date, comment='承诺交期')

    # 收货状态
    received_qty = Column(Numeric(10, 4), default=0, comment='已收货数量')
    qualified_qty = Column(Numeric(10, 4), default=0, comment='合格数量')
    rejected_qty = Column(Numeric(10, 4), default=0, comment='不合格数量')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    remark = Column(Text, comment='备注')

    # 关系
    order = relationship('PurchaseOrder', back_populates='items')
    material = relationship('Material')
    receipt_items = relationship('GoodsReceiptItem', back_populates='order_item', lazy='dynamic')

    __table_args__ = (
        Index('idx_poi_order', 'order_id'),
        Index('idx_poi_material', 'material_id'),
    )


class GoodsReceipt(Base, TimestampMixin):
    """收货单表"""
    __tablename__ = 'goods_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_no = Column(String(50), unique=True, nullable=False, comment='收货单号')
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False, comment='采购订单ID')
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='供应商ID')

    # 收货信息
    receipt_date = Column(Date, nullable=False, comment='收货日期')
    receipt_type = Column(String(20), default='NORMAL', comment='收货类型')
    delivery_note_no = Column(String(100), comment='送货单号')

    # 物流信息
    logistics_company = Column(String(100), comment='物流公司')
    tracking_no = Column(String(100), comment='运单号')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 质检
    inspect_status = Column(String(20), default='PENDING', comment='质检状态')
    inspected_at = Column(DateTime, comment='质检时间')
    inspected_by = Column(Integer, ForeignKey('users.id'), comment='质检人')

    # 入库
    warehoused_at = Column(DateTime, comment='入库时间')
    warehoused_by = Column(Integer, ForeignKey('users.id'), comment='入库人')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    order = relationship('PurchaseOrder', back_populates='receipts')
    # supplier = relationship('Supplier')  # 已禁用 - Supplier 是废弃模型
    items = relationship('GoodsReceiptItem', back_populates='receipt', lazy='dynamic')

    __table_args__ = (
        Index('idx_gr_order', 'order_id'),
        Index('idx_gr_supplier', 'supplier_id'),
        Index('idx_gr_status', 'status'),
    )

    def __repr__(self):
        return f'<GoodsReceipt {self.receipt_no}>'


class GoodsReceiptItem(Base, TimestampMixin):
    """收货单明细表"""
    __tablename__ = 'goods_receipt_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey('goods_receipts.id'), nullable=False, comment='收货单ID')
    order_item_id = Column(Integer, ForeignKey('purchase_order_items.id'), nullable=False, comment='订单行ID')

    # 物料信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')

    # 数量
    delivery_qty = Column(Numeric(10, 4), nullable=False, comment='送货数量')
    received_qty = Column(Numeric(10, 4), default=0, comment='实收数量')

    # 质检
    inspect_qty = Column(Numeric(10, 4), default=0, comment='送检数量')
    qualified_qty = Column(Numeric(10, 4), default=0, comment='合格数量')
    rejected_qty = Column(Numeric(10, 4), default=0, comment='不合格数量')
    inspect_result = Column(String(20), comment='质检结果')
    inspect_note = Column(Text, comment='质检说明')

    # 入库
    warehoused_qty = Column(Numeric(10, 4), default=0, comment='入库数量')
    warehouse_location = Column(String(100), comment='库位')

    amount = Column(Numeric(14, 2), default=0, comment='金额')
    remark = Column(Text, comment='备注')

    # 关系
    receipt = relationship('GoodsReceipt', back_populates='items')
    order_item = relationship('PurchaseOrderItem', back_populates='receipt_items')

    __table_args__ = (
        Index('idx_gri_receipt', 'receipt_id'),
        Index('idx_gri_order_item', 'order_item_id'),
    )


class PurchaseRequest(Base, TimestampMixin):
    """采购申请单表"""
    __tablename__ = 'purchase_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_no = Column(String(50), unique=True, nullable=False, comment='申请单号')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')
    supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='供应商ID')

    # 申请信息
    request_type = Column(String(20), default='NORMAL', comment='申请类型')
    source_type = Column(String(20), default='MANUAL', comment='来源类型（BOM/SHORTAGE/MANUAL）')
    source_id = Column(Integer, comment='来源业务ID')
    request_reason = Column(Text, comment='申请原因')
    required_date = Column(Date, comment='需求日期')

    # 金额
    total_amount = Column(Numeric(14, 2), default=0, comment='总金额')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 审批
    submitted_at = Column(DateTime, comment='提交时间')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')
    approval_note = Column(Text, comment='审批意见')
    auto_po_created = Column(Boolean, default=False, comment='是否已自动生成采购订单')
    auto_po_created_at = Column(DateTime, comment='自动下单时间')
    auto_po_created_by = Column(Integer, ForeignKey('users.id'), comment='自动下单人')

    # 申请人
    requested_by = Column(Integer, ForeignKey('users.id'), comment='申请人')
    requested_at = Column(DateTime, comment='申请时间')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    # supplier = relationship('Supplier')  # 已禁用 - Supplier 是废弃模型
    items = relationship('PurchaseRequestItem', back_populates='request', lazy='dynamic', cascade='all, delete-orphan')
    approver = relationship('User', foreign_keys=[approved_by])
    requester = relationship('User', foreign_keys=[requested_by])
    creator = relationship('User', foreign_keys=[created_by])
    auto_po_creator = relationship('User', foreign_keys=[auto_po_created_by])
    orders = relationship('PurchaseOrder', back_populates='source_request', lazy='dynamic')

    __table_args__ = (
        Index('idx_pr_no', 'request_no'),
        Index('idx_pr_project', 'project_id'),
        Index('idx_pr_status', 'status'),
        Index('idx_pr_supplier', 'supplier_id'),
        Index('idx_pr_source', 'source_type'),
    )

    def __repr__(self):
        return f'<PurchaseRequest {self.request_no}>'


class PurchaseRequestItem(Base, TimestampMixin):
    """采购申请明细表"""
    __tablename__ = 'purchase_request_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('purchase_requests.id'), nullable=False, comment='申请单ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='BOM行ID')
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')

    # 物料信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')

    # 数量与价格
    quantity = Column(Numeric(10, 4), nullable=False, comment='申请数量')
    unit_price = Column(Numeric(12, 4), default=0, comment='预估单价')
    amount = Column(Numeric(14, 2), default=0, comment='金额')

    # 需求日期
    required_date = Column(Date, comment='需求日期')

    # 已采购数量
    ordered_qty = Column(Numeric(10, 4), default=0, comment='已采购数量')

    remark = Column(Text, comment='备注')

    # 关系
    request = relationship('PurchaseRequest', back_populates='items')
    bom_item = relationship('BomItem')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_pri_request', 'request_id'),
        Index('idx_pri_material', 'material_id'),
    )
