# -*- coding: utf-8 -*-
"""
外协管理模块模型
"""

from sqlalchemy import (
    JSON,
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


class OutsourcingOrder(Base, TimestampMixin):
    """外协订单表"""
    __tablename__ = 'outsourcing_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment='外协订单号')
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='外协商ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')

    # 订单信息
    order_date = Column(Date, comment='下单日期')
    order_type = Column(String(20), nullable=False, comment='订单类型')
    order_title = Column(String(200), nullable=False, comment='订单标题')
    order_description = Column(Text, comment='订单说明')

    # 金额
    total_amount = Column(Numeric(14, 2), default=0, comment='总金额')
    tax_rate = Column(Numeric(5, 2), default=13, comment='税率')
    tax_amount = Column(Numeric(14, 2), default=0, comment='税额')
    amount_with_tax = Column(Numeric(14, 2), default=0, comment='含税金额')

    # 时间要求
    required_date = Column(Date, comment='要求交期')
    estimated_date = Column(Date, comment='预计交期')
    actual_date = Column(Date, comment='实际交期')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 付款状态
    payment_status = Column(String(20), default='UNPAID', comment='付款状态')
    paid_amount = Column(Numeric(14, 2), default=0, comment='已付金额')

    # 签约
    contract_no = Column(String(100), comment='合同编号')
    contract_file = Column(String(500), comment='合同文件路径')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    vendor = relationship('Vendor', back_populates='outsourcing_orders')
    project = relationship('Project')
    machine = relationship('Machine')
    items = relationship('OutsourcingOrderItem', back_populates='order', lazy='dynamic')
    deliveries = relationship('OutsourcingDelivery', back_populates='order', lazy='dynamic')
    progress_records = relationship('OutsourcingProgress', back_populates='order', lazy='dynamic')

    __table_args__ = (
        Index('idx_os_order_vendor', 'vendor_id'),
        Index('idx_os_order_project', 'project_id'),
        Index('idx_os_order_status', 'status'),
    )

    def __repr__(self):
        return f'<OutsourcingOrder {self.order_no}>'


class OutsourcingOrderItem(Base, TimestampMixin):
    """外协订单明细表"""
    __tablename__ = 'outsourcing_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('outsourcing_orders.id'), nullable=False, comment='外协订单ID')
    item_no = Column(Integer, nullable=False, comment='行号')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    drawing_no = Column(String(100), comment='图号')

    # 加工信息
    process_type = Column(String(50), comment='加工类型')
    process_content = Column(Text, comment='加工内容')
    process_requirements = Column(Text, comment='工艺要求')

    # 数量与单价
    unit = Column(String(20), default='件', comment='单位')
    quantity = Column(Numeric(10, 4), nullable=False, comment='数量')
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    amount = Column(Numeric(14, 2), default=0, comment='金额')

    # 来料信息
    material_provided = Column(Boolean, default=False, comment='是否来料加工')
    provided_quantity = Column(Numeric(10, 4), default=0, comment='来料数量')
    provided_date = Column(Date, comment='来料日期')

    # 交付信息
    delivered_quantity = Column(Numeric(10, 4), default=0, comment='已交付数量')
    qualified_quantity = Column(Numeric(10, 4), default=0, comment='合格数量')
    rejected_quantity = Column(Numeric(10, 4), default=0, comment='不合格数量')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    remark = Column(Text, comment='备注')

    # 关系
    order = relationship('OutsourcingOrder', back_populates='items')
    material = relationship('Material')
    delivery_items = relationship('OutsourcingDeliveryItem', back_populates='order_item', lazy='dynamic')

    __table_args__ = (
        Index('idx_os_item_order', 'order_id'),
        Index('idx_os_item_material', 'material_id'),
    )


class OutsourcingDelivery(Base, TimestampMixin):
    """外协交付记录表"""
    __tablename__ = 'outsourcing_deliveries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_no = Column(String(50), unique=True, nullable=False, comment='交付单号')
    order_id = Column(Integer, ForeignKey('outsourcing_orders.id'), nullable=False, comment='外协订单ID')
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='外协商ID')

    # 交付信息
    delivery_date = Column(Date, nullable=False, comment='交付日期')
    delivery_type = Column(String(20), default='NORMAL', comment='交付类型')
    delivery_person = Column(String(50), comment='送货人')
    receiver = Column(String(50), comment='收货人')

    # 物流信息
    logistics_company = Column(String(100), comment='物流公司')
    tracking_no = Column(String(100), comment='运单号')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    received_at = Column(DateTime, comment='收货时间')
    received_by = Column(Integer, ForeignKey('users.id'), comment='收货人ID')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    order = relationship('OutsourcingOrder', back_populates='deliveries')
    vendor = relationship('Vendor', foreign_keys=[vendor_id])
    items = relationship('OutsourcingDeliveryItem', back_populates='delivery', lazy='dynamic')

    __table_args__ = (
        Index('idx_os_delivery_order', 'order_id'),
        Index('idx_os_delivery_vendor', 'vendor_id'),
        Index('idx_os_delivery_status', 'status'),
    )

    def __repr__(self):
        return f'<OutsourcingDelivery {self.delivery_no}>'


class OutsourcingDeliveryItem(Base, TimestampMixin):
    """外协交付明细表"""
    __tablename__ = 'outsourcing_delivery_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_id = Column(Integer, ForeignKey('outsourcing_deliveries.id'), nullable=False, comment='交付单ID')
    order_item_id = Column(Integer, ForeignKey('outsourcing_order_items.id'), nullable=False, comment='订单明细ID')

    # 物料信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')

    # 数量
    delivery_quantity = Column(Numeric(10, 4), nullable=False, comment='交付数量')
    received_quantity = Column(Numeric(10, 4), default=0, comment='实收数量')

    # 质检结果
    inspect_status = Column(String(20), default='PENDING', comment='质检状态')
    qualified_quantity = Column(Numeric(10, 4), default=0, comment='合格数量')
    rejected_quantity = Column(Numeric(10, 4), default=0, comment='不合格数量')

    remark = Column(Text, comment='备注')

    # 关系
    delivery = relationship('OutsourcingDelivery', back_populates='items')
    order_item = relationship('OutsourcingOrderItem', back_populates='delivery_items')
    inspections = relationship('OutsourcingInspection', back_populates='delivery_item', lazy='dynamic')

    __table_args__ = (
        Index('idx_os_deli_item_delivery', 'delivery_id'),
    )


class OutsourcingInspection(Base, TimestampMixin):
    """外协质检记录表"""
    __tablename__ = 'outsourcing_inspections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_no = Column(String(50), unique=True, nullable=False, comment='质检单号')
    delivery_id = Column(Integer, ForeignKey('outsourcing_deliveries.id'), nullable=False, comment='交付单ID')
    delivery_item_id = Column(Integer, ForeignKey('outsourcing_delivery_items.id'), nullable=False, comment='交付明细ID')

    # 质检信息
    inspect_type = Column(String(20), default='INCOMING', comment='质检类型')
    inspect_date = Column(Date, nullable=False, comment='质检日期')
    inspector_id = Column(Integer, ForeignKey('users.id'), comment='质检员ID')
    inspector_name = Column(String(50), comment='质检员姓名')

    # 检验数量
    inspect_quantity = Column(Numeric(10, 4), nullable=False, comment='送检数量')
    sample_quantity = Column(Numeric(10, 4), default=0, comment='抽检数量')
    qualified_quantity = Column(Numeric(10, 4), default=0, comment='合格数量')
    rejected_quantity = Column(Numeric(10, 4), default=0, comment='不合格数量')

    # 结果
    inspect_result = Column(String(20), comment='质检结果')
    pass_rate = Column(Numeric(5, 2), default=0, comment='合格率')

    # 不良信息
    defect_description = Column(Text, comment='不良描述')
    defect_type = Column(String(50), comment='不良类型')
    defect_images = Column(JSON, comment='不良图片')

    # 处理
    disposition = Column(String(20), comment='处置方式')
    disposition_note = Column(Text, comment='处理说明')

    remark = Column(Text, comment='备注')

    # 关系
    delivery = relationship('OutsourcingDelivery')
    delivery_item = relationship('OutsourcingDeliveryItem', back_populates='inspections')

    __table_args__ = (
        Index('idx_os_inspect_delivery', 'delivery_id'),
        Index('idx_os_inspect_result', 'inspect_result'),
    )

    def __repr__(self):
        return f'<OutsourcingInspection {self.inspection_no}>'


class OutsourcingPayment(Base, TimestampMixin):
    """外协付款记录表"""
    __tablename__ = 'outsourcing_payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_no = Column(String(50), unique=True, nullable=False, comment='付款单号')
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='外协商ID')
    order_id = Column(Integer, ForeignKey('outsourcing_orders.id'), comment='外协订单ID')

    # 付款信息
    payment_type = Column(String(20), nullable=False, comment='付款类型')
    payment_amount = Column(Numeric(14, 2), nullable=False, comment='付款金额')
    payment_date = Column(Date, comment='付款日期')
    payment_method = Column(String(20), comment='付款方式')

    # 发票信息
    invoice_no = Column(String(100), comment='发票号')
    invoice_amount = Column(Numeric(14, 2), comment='发票金额')
    invoice_date = Column(Date, comment='发票日期')

    # 审批
    status = Column(String(20), default='DRAFT', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    vendor = relationship('Vendor', foreign_keys=[vendor_id])
    order = relationship('OutsourcingOrder')

    __table_args__ = (
        Index('idx_os_payment_vendor', 'vendor_id'),
        Index('idx_os_payment_order', 'order_id'),
        Index('idx_os_payment_status', 'status'),
    )

    def __repr__(self):
        return f'<OutsourcingPayment {self.payment_no}>'


class OutsourcingEvaluation(Base, TimestampMixin):
    """外协商评价表"""
    __tablename__ = 'outsourcing_evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='外协商ID')
    order_id = Column(Integer, ForeignKey('outsourcing_orders.id'), comment='关联订单')
    eval_period = Column(String(20), comment='评价周期')

    # 评分
    quality_score = Column(Numeric(3, 2), default=0, comment='质量评分')
    delivery_score = Column(Numeric(3, 2), default=0, comment='交期评分')
    price_score = Column(Numeric(3, 2), default=0, comment='价格评分')
    service_score = Column(Numeric(3, 2), default=0, comment='服务评分')
    overall_score = Column(Numeric(3, 2), default=0, comment='综合评分')

    # 评价内容
    advantages = Column(Text, comment='优点')
    disadvantages = Column(Text, comment='不足')
    improvement = Column(Text, comment='改进建议')

    # 评价人
    evaluator_id = Column(Integer, ForeignKey('users.id'), comment='评价人')
    evaluated_at = Column(DateTime, comment='评价时间')

    # 关系
    vendor = relationship('Vendor', foreign_keys=[vendor_id], back_populates='outsourcing_evaluations')

    __table_args__ = (
        Index('idx_os_eval_vendor', 'vendor_id'),
        Index('idx_os_eval_period', 'eval_period'),
    )


class OutsourcingProgress(Base, TimestampMixin):
    """外协进度跟踪表"""
    __tablename__ = 'outsourcing_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('outsourcing_orders.id'), nullable=False, comment='外协订单ID')
    order_item_id = Column(Integer, ForeignKey('outsourcing_order_items.id'), comment='订单明细ID')

    # 进度信息
    report_date = Column(Date, nullable=False, comment='报告日期')
    progress_pct = Column(Integer, default=0, comment='进度百分比')
    completed_quantity = Column(Numeric(10, 4), default=0, comment='完成数量')

    # 状态
    current_process = Column(String(100), comment='当前工序')
    next_process = Column(String(100), comment='下一工序')
    estimated_complete = Column(Date, comment='预计完成日期')

    # 问题
    issues = Column(Text, comment='问题说明')
    risk_level = Column(String(20), comment='风险级别')

    # 附件
    attachments = Column(JSON, comment='附件')

    reported_by = Column(Integer, ForeignKey('users.id'), comment='报告人')

    # 关系
    order = relationship('OutsourcingOrder', back_populates='progress_records')

    __table_args__ = (
        Index('idx_os_progress_order', 'order_id'),
        Index('idx_os_progress_date', 'report_date'),
    )


# ---------------------------------------------------------------------------
# 兼容层：旧 OutsourcingVendor 模型（现统一为 Vendor）
# ---------------------------------------------------------------------------
from app.models.vendor import Vendor as OutsourcingVendor  # noqa: F401
