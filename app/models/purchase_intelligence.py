# -*- coding: utf-8 -*-
"""
智能采购管理模块 - 数据模型
包括采购建议、供应商绩效、供应商报价等
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin


class PurchaseSuggestion(Base, TimestampMixin, TenantMixin):
    """采购建议表"""
    __tablename__ = 'purchase_suggestions'
    __table_args__ = (
        Index('idx_ps_material', 'material_id'),
        Index('idx_ps_status', 'status'),
        Index('idx_ps_source', 'source_type'),
        Index('idx_ps_tenant', 'tenant_id'),
        Index('idx_ps_suggested_supplier', 'suggested_supplier_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_no = Column(String(50), unique=True, nullable=False, comment='建议编号')
    
    # 租户ID（多租户支持）
    tenant_id = Column(Integer, nullable=False, default=1, comment='租户ID')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')
    
    # 建议数量
    suggested_qty = Column(Numeric(10, 4), nullable=False, comment='建议数量')
    current_stock = Column(Numeric(10, 4), default=0, comment='当前库存')
    safety_stock = Column(Numeric(10, 4), default=0, comment='安全库存')
    
    # 建议来源
    source_type = Column(String(30), nullable=False, comment='来源类型：SHORTAGE/SAFETY_STOCK/FORECAST/MANUAL')
    source_id = Column(Integer, comment='来源业务ID（如短缺ID、项目ID等）')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    
    # 需求信息
    required_date = Column(Date, comment='需求日期')
    urgency_level = Column(String(20), default='NORMAL', comment='紧急程度：LOW/NORMAL/HIGH/URGENT')
    
    # AI推荐供应商
    suggested_supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='推荐供应商ID')
    ai_confidence = Column(Numeric(5, 2), comment='AI推荐置信度(0-100)')
    recommendation_reason = Column(JSON, comment='推荐理由（JSON格式）')
    alternative_suppliers = Column(JSON, comment='备选供应商列表（JSON格式）')
    
    # 预估价格
    estimated_unit_price = Column(Numeric(12, 4), comment='预估单价')
    estimated_total_amount = Column(Numeric(14, 2), comment='预估总额')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态：PENDING/APPROVED/REJECTED/ORDERED')
    
    # 审批信息
    reviewed_by = Column(Integer, ForeignKey('users.id'), comment='审核人')
    reviewed_at = Column(DateTime, comment='审核时间')
    review_note = Column(Text, comment='审核意见')
    
    # 转订单信息
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), comment='生成的采购订单ID')
    ordered_at = Column(DateTime, comment='下单时间')
    
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')
    
    # 关系
    material = relationship('Material')
    suggested_supplier = relationship('Vendor', foreign_keys=[suggested_supplier_id])
    project = relationship('Project')
    reviewer = relationship('User', foreign_keys=[reviewed_by])
    creator = relationship('User', foreign_keys=[created_by])
    purchase_order = relationship('PurchaseOrder')
    
    def __repr__(self):
        return f'<PurchaseSuggestion {self.suggestion_no}>'


class SupplierQuotation(Base, TimestampMixin, TenantMixin):
    """供应商报价表"""
    __tablename__ = 'supplier_quotations'
    __table_args__ = (
        Index('idx_sq_supplier', 'supplier_id'),
        Index('idx_sq_material', 'material_id'),
        Index('idx_sq_status', 'status'),
        Index('idx_sq_tenant', 'tenant_id'),
        Index('idx_sq_valid_date', 'valid_from', 'valid_to'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quotation_no = Column(String(50), unique=True, nullable=False, comment='报价单号')
    
    # 租户ID
    tenant_id = Column(Integer, nullable=False, default=1, comment='租户ID')
    
    # 供应商和物料
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='供应商ID')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    
    # 报价信息
    unit_price = Column(Numeric(12, 4), nullable=False, comment='单价')
    currency = Column(String(10), default='CNY', comment='币种')
    min_order_qty = Column(Numeric(10, 4), default=1, comment='最小订购量')
    lead_time_days = Column(Integer, default=0, comment='交货周期（天）')
    
    # 有效期
    valid_from = Column(Date, nullable=False, comment='有效期起')
    valid_to = Column(Date, nullable=False, comment='有效期止')
    
    # 附加信息
    payment_terms = Column(String(100), comment='付款条款')
    warranty_period = Column(String(50), comment='质保期')
    tax_rate = Column(Numeric(5, 2), default=13, comment='税率(%)')
    
    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态：ACTIVE/EXPIRED/REJECTED')
    is_selected = Column(Boolean, default=False, comment='是否被选中')
    
    # 询价关联
    inquiry_id = Column(Integer, comment='询价单ID（预留）')
    
    # 附件
    attachments = Column(JSON, comment='附件列表（JSON格式）')
    
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')
    
    # 关系
    supplier = relationship('Vendor')
    material = relationship('Material')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<SupplierQuotation {self.quotation_no}>'


class SupplierPerformance(Base, TimestampMixin, TenantMixin):
    """供应商绩效评估表"""
    __tablename__ = 'supplier_performances'
    __table_args__ = (
        Index('idx_sp_supplier', 'supplier_id'),
        Index('idx_sp_period', 'evaluation_period'),
        Index('idx_sp_tenant', 'tenant_id'),
        Index('idx_sp_score', 'overall_score'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 租户ID
    tenant_id = Column(Integer, nullable=False, default=1, comment='租户ID')
    
    # 供应商
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, comment='供应商ID')
    supplier_code = Column(String(50), nullable=False, comment='供应商编码')
    supplier_name = Column(String(200), nullable=False, comment='供应商名称')
    
    # 评估期间
    evaluation_period = Column(String(20), nullable=False, comment='评估期间：YYYY-MM')
    period_start = Column(Date, nullable=False, comment='期间开始日期')
    period_end = Column(Date, nullable=False, comment='期间结束日期')
    
    # 统计数据
    total_orders = Column(Integer, default=0, comment='订单总数')
    total_amount = Column(Numeric(14, 2), default=0, comment='采购总额')
    
    # 准时交货率（0-100）
    on_time_delivery_rate = Column(Numeric(5, 2), default=0, comment='准时交货率(%)')
    on_time_orders = Column(Integer, default=0, comment='准时订单数')
    late_orders = Column(Integer, default=0, comment='延迟订单数')
    avg_delay_days = Column(Numeric(6, 2), default=0, comment='平均延迟天数')
    
    # 质量合格率（0-100）
    quality_pass_rate = Column(Numeric(5, 2), default=0, comment='质量合格率(%)')
    total_received_qty = Column(Numeric(12, 4), default=0, comment='收货总数')
    qualified_qty = Column(Numeric(12, 4), default=0, comment='合格数量')
    rejected_qty = Column(Numeric(12, 4), default=0, comment='不合格数量')
    
    # 价格竞争力（0-100，越高越有竞争力）
    price_competitiveness = Column(Numeric(5, 2), default=0, comment='价格竞争力评分')
    avg_price_vs_market = Column(Numeric(6, 2), default=0, comment='平均价格相对市场价(%)，负数表示低于市场价')
    
    # 响应速度评分（0-100）
    response_speed_score = Column(Numeric(5, 2), default=0, comment='响应速度评分')
    avg_response_hours = Column(Numeric(6, 2), default=0, comment='平均响应时间（小时）')
    
    # 服务评分（0-100，可选）
    service_score = Column(Numeric(5, 2), comment='服务评分')
    
    # 综合评分（0-100）
    overall_score = Column(Numeric(5, 2), nullable=False, default=0, comment='综合评分')
    rating = Column(String(2), comment='等级：A+/A/B/C/D')
    
    # 权重配置（JSON格式，用于记录当次评估的权重）
    weight_config = Column(JSON, comment='评分权重配置')
    
    # 详细数据（JSON格式，保存原始统计数据）
    detail_data = Column(JSON, comment='详细数据')
    
    # 评估状态
    status = Column(String(20), default='CALCULATED', comment='状态：CALCULATED/REVIEWED/PUBLISHED')
    
    # 评审信息
    reviewed_by = Column(Integer, ForeignKey('users.id'), comment='评审人')
    reviewed_at = Column(DateTime, comment='评审时间')
    review_note = Column(Text, comment='评审意见')
    
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')
    
    # 关系
    supplier = relationship('Vendor')
    reviewer = relationship('User', foreign_keys=[reviewed_by])
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<SupplierPerformance {self.supplier_code} {self.evaluation_period}>'


class PurchaseOrderTracking(Base, TimestampMixin, TenantMixin):
    """采购订单跟踪记录表"""
    __tablename__ = 'purchase_order_trackings'
    __table_args__ = (
        Index('idx_pot_order', 'order_id'),
        Index('idx_pot_tenant', 'tenant_id'),
        Index('idx_pot_event_type', 'event_type'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 租户ID
    tenant_id = Column(Integer, nullable=False, default=1, comment='租户ID')
    
    # 订单信息
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False, comment='采购订单ID')
    order_no = Column(String(50), nullable=False, comment='订单编号')
    
    # 跟踪事件
    event_type = Column(String(30), nullable=False, comment='事件类型：CREATED/SUBMITTED/APPROVED/CONFIRMED/SHIPPED/RECEIVED/COMPLETED')
    event_time = Column(DateTime, nullable=False, comment='事件时间')
    event_description = Column(Text, comment='事件描述')
    
    # 状态变更
    old_status = Column(String(20), comment='原状态')
    new_status = Column(String(20), comment='新状态')
    
    # 附加信息
    tracking_no = Column(String(100), comment='物流单号')
    logistics_company = Column(String(100), comment='物流公司')
    estimated_arrival = Column(Date, comment='预计到货日期')
    
    # 附件和备注
    attachments = Column(JSON, comment='附件列表')
    note = Column(Text, comment='备注')
    
    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), comment='操作人')
    
    # 关系
    order = relationship('PurchaseOrder')
    operator = relationship('User')
    
    def __repr__(self):
        return f'<PurchaseOrderTracking {self.order_no} {self.event_type}>'
