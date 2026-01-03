# -*- coding: utf-8 -*-
"""
物料管理模块模型
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Index
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class MaterialCategory(Base, TimestampMixin):
    """物料分类表"""
    __tablename__ = 'material_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_code = Column(String(50), unique=True, nullable=False, comment='分类编码')
    category_name = Column(String(100), nullable=False, comment='分类名称')
    parent_id = Column(Integer, ForeignKey('material_categories.id'), comment='父分类ID')
    level = Column(Integer, default=1, comment='层级')
    full_path = Column(String(500), comment='完整路径')
    description = Column(Text, comment='描述')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 自引用关系
    parent = relationship('MaterialCategory', remote_side=[id], backref='children')
    materials = relationship('Material', back_populates='category')

    def __repr__(self):
        return f'<MaterialCategory {self.category_code}>'


class Material(Base, TimestampMixin):
    """物料表"""
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(50), unique=True, nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    category_id = Column(Integer, ForeignKey('material_categories.id'), comment='分类ID')

    # 规格信息
    specification = Column(String(500), comment='规格型号')
    brand = Column(String(100), comment='品牌')
    unit = Column(String(20), default='件', comment='单位')
    drawing_no = Column(String(100), comment='图号')

    # 类型
    material_type = Column(String(20), comment='物料类型')
    source_type = Column(String(20), default='PURCHASE', comment='来源类型')

    # 价格
    standard_price = Column(Numeric(12, 4), default=0, comment='标准价格')
    last_price = Column(Numeric(12, 4), default=0, comment='最近采购价')
    currency = Column(String(10), default='CNY', comment='币种')

    # 库存
    safety_stock = Column(Numeric(10, 4), default=0, comment='安全库存')
    current_stock = Column(Numeric(10, 4), default=0, comment='当前库存')

    # 采购参数
    lead_time_days = Column(Integer, default=0, comment='采购周期(天)')
    min_order_qty = Column(Numeric(10, 4), default=1, comment='最小订购量')
    default_supplier_id = Column(Integer, ForeignKey('suppliers.id'), comment='默认供应商')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_key_material = Column(Boolean, default=False, comment='是否关键物料')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    category = relationship('MaterialCategory', back_populates='materials')
    default_supplier = relationship('Supplier', foreign_keys=[default_supplier_id])
    suppliers = relationship('MaterialSupplier', back_populates='material', lazy='dynamic')
    bom_items = relationship('BomItem', back_populates='material', lazy='dynamic')

    __table_args__ = (
        Index('idx_material_category', 'category_id'),
        Index('idx_material_type', 'material_type'),
    )

    def __repr__(self):
        return f'<Material {self.material_code}>'


class Supplier(Base, TimestampMixin):
    """供应商表"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_code = Column(String(50), unique=True, nullable=False, comment='供应商编码')
    supplier_name = Column(String(200), nullable=False, comment='供应商名称')
    supplier_short_name = Column(String(50), comment='简称')
    supplier_type = Column(String(20), comment='供应商类型')

    # 联系信息
    contact_person = Column(String(50), comment='联系人')
    contact_phone = Column(String(30), comment='联系电话')
    contact_email = Column(String(100), comment='邮箱')
    address = Column(String(500), comment='地址')

    # 资质
    business_license = Column(String(100), comment='营业执照号')
    qualification = Column(Text, comment='资质认证JSON')

    # 评价
    quality_rating = Column(Numeric(3, 2), default=0, comment='质量评分')
    delivery_rating = Column(Numeric(3, 2), default=0, comment='交期评分')
    service_rating = Column(Numeric(3, 2), default=0, comment='服务评分')
    overall_rating = Column(Numeric(3, 2), default=0, comment='综合评分')
    supplier_level = Column(String(1), default='B', comment='供应商等级')

    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态')
    cooperation_start = Column(Date, comment='合作开始日期')
    last_order_date = Column(Date, comment='最后订单日期')

    # 财务信息
    bank_name = Column(String(100), comment='开户行')
    bank_account = Column(String(50), comment='银行账号')
    tax_number = Column(String(50), comment='税号')
    payment_terms = Column(String(50), comment='付款条款')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    materials = relationship('MaterialSupplier', back_populates='supplier', lazy='dynamic')
    purchase_orders = relationship('PurchaseOrder', back_populates='supplier', lazy='dynamic')

    __table_args__ = (
        Index('idx_supplier_type', 'supplier_type'),
        Index('idx_supplier_status', 'status'),
    )

    def __repr__(self):
        return f'<Supplier {self.supplier_code}>'


class MaterialSupplier(Base, TimestampMixin):
    """物料供应商关联表"""
    __tablename__ = 'material_suppliers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False, comment='供应商ID')

    # 供应信息
    supplier_material_code = Column(String(100), comment='供应商物料编码')
    price = Column(Numeric(12, 4), default=0, comment='采购价格')
    currency = Column(String(10), default='CNY', comment='币种')
    lead_time_days = Column(Integer, default=0, comment='交货周期(天)')
    min_order_qty = Column(Numeric(10, 4), default=1, comment='最小订购量')

    # 状态
    is_preferred = Column(Boolean, default=False, comment='是否首选')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 有效期
    valid_from = Column(Date, comment='有效期起')
    valid_to = Column(Date, comment='有效期止')

    remark = Column(Text, comment='备注')

    # 关系
    material = relationship('Material', back_populates='suppliers')
    supplier = relationship('Supplier', back_populates='materials')

    __table_args__ = (
        Index('idx_ms_material', 'material_id'),
        Index('idx_ms_supplier', 'supplier_id'),
    )


class BomHeader(Base, TimestampMixin):
    """BOM表头"""
    __tablename__ = 'bom_headers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_no = Column(String(50), unique=True, nullable=False, comment='BOM编号')
    bom_name = Column(String(200), nullable=False, comment='BOM名称')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')

    # 版本
    version = Column(String(20), default='1.0', comment='版本号')
    is_latest = Column(Boolean, default=True, comment='是否最新版本')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 统计
    total_items = Column(Integer, default=0, comment='物料行数')
    total_amount = Column(Numeric(14, 2), default=0, comment='总金额')

    # 审批
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine', back_populates='bom_headers')
    items = relationship('BomItem', back_populates='header', lazy='dynamic')

    __table_args__ = (
        Index('idx_bom_project', 'project_id'),
        Index('idx_bom_machine', 'machine_id'),
    )

    def __repr__(self):
        return f'<BomHeader {self.bom_no}>'


class BomItem(Base, TimestampMixin):
    """BOM明细"""
    __tablename__ = 'bom_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_id = Column(Integer, ForeignKey('bom_headers.id'), nullable=False, comment='BOM ID')
    item_no = Column(Integer, nullable=False, comment='行号')
    parent_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='父级行ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    drawing_no = Column(String(100), comment='图号')
    unit = Column(String(20), default='件', comment='单位')

    # 数量
    quantity = Column(Numeric(10, 4), nullable=False, comment='需求数量')
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    amount = Column(Numeric(14, 2), default=0, comment='金额')

    # 来源
    source_type = Column(String(20), default='PURCHASE', comment='来源类型')
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), comment='供应商ID')

    # 采购状态
    required_date = Column(Date, comment='需求日期')
    purchased_qty = Column(Numeric(10, 4), default=0, comment='已采购数量')
    received_qty = Column(Numeric(10, 4), default=0, comment='已到货数量')

    # 层级
    level = Column(Integer, default=1, comment='BOM层级')
    sort_order = Column(Integer, default=0, comment='排序')

    is_key_item = Column(Boolean, default=False, comment='是否关键物料')
    remark = Column(Text, comment='备注')

    # 关系
    header = relationship('BomHeader', back_populates='items')
    material = relationship('Material', back_populates='bom_items')
    parent = relationship('BomItem', remote_side=[id], backref='children')

    __table_args__ = (
        Index('idx_bom_item_bom', 'bom_id'),
        Index('idx_bom_item_material', 'material_id'),
    )


class MaterialShortage(Base, TimestampMixin):
    """物料短缺预警表"""
    __tablename__ = 'material_shortages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='BOM行ID')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')

    # 短缺信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    required_qty = Column(Numeric(10, 4), nullable=False, comment='需求数量')
    available_qty = Column(Numeric(10, 4), default=0, comment='可用数量')
    shortage_qty = Column(Numeric(10, 4), nullable=False, comment='短缺数量')
    required_date = Column(Date, comment='需求日期')

    # 状态
    status = Column(String(20), default='OPEN', comment='状态')
    alert_level = Column(String(20), default='WARNING', comment='预警级别')

    # 处理
    solution = Column(Text, comment='解决方案')
    handler_id = Column(Integer, ForeignKey('users.id'), comment='处理人')
    resolved_at = Column(DateTime, comment='解决时间')

    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_shortage_project', 'project_id'),
        Index('idx_shortage_material', 'material_id'),
        Index('idx_shortage_status', 'status'),
    )
