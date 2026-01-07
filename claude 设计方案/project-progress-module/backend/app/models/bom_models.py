"""
BOM管理模块 - 数据模型定义
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text
from sqlalchemy import ForeignKey, Index, Boolean, Numeric, SmallInteger
from sqlalchemy.orm import relationship

from app.models.models import Base


class Material(Base):
    """物料主数据表"""
    __tablename__ = "material"

    material_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="物料ID")
    material_code = Column(String(30), unique=True, nullable=False, comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")
    specification = Column(String(200), nullable=True, comment="规格型号")
    brand = Column(String(50), nullable=True, comment="品牌")
    category = Column(String(20), nullable=False, comment="大类：ME/EL/PN/ST/OT/TR")
    sub_category = Column(String(50), nullable=True, comment="子类别")
    unit = Column(String(20), default="pcs", comment="单位")
    reference_price = Column(Numeric(12, 2), nullable=True, comment="参考单价")
    default_supplier_id = Column(BigInteger, nullable=True, comment="默认供应商ID")
    default_supplier_name = Column(String(100), nullable=True, comment="默认供应商")
    lead_time = Column(Integer, default=7, comment="标准采购周期(天)")
    min_order_qty = Column(Numeric(10, 2), default=1, comment="最小起订量")
    is_standard = Column(SmallInteger, default=0, comment="是否标准件")
    status = Column(String(20), default="启用", comment="状态")
    remark = Column(String(500), nullable=True, comment="备注")
    created_by = Column(BigInteger, nullable=False, comment="创建人ID")
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, comment="是否删除")

    __table_args__ = (
        Index("idx_material_category", "category"),
        Index("idx_material_name", "material_name"),
    )


class BomHeader(Base):
    """BOM头表"""
    __tablename__ = "bom_header"

    bom_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="BOM ID")
    project_id = Column(BigInteger, nullable=False, comment="项目ID")
    project_code = Column(String(30), nullable=False, comment="项目编号")
    machine_no = Column(String(30), nullable=False, comment="机台号")
    machine_name = Column(String(100), nullable=True, comment="机台名称")
    bom_type = Column(String(20), default="整机", comment="BOM类型：整机/模块/备件")
    current_version = Column(String(10), default="V1.0", comment="当前版本")
    status = Column(String(20), default="草稿", comment="状态：草稿/评审中/已发布/已冻结")
    total_items = Column(Integer, default=0, comment="物料总数")
    total_cost = Column(Numeric(14, 2), default=0, comment="预估总成本")
    kit_rate = Column(Numeric(5, 2), default=0, comment="齐套率%")
    designer_id = Column(BigInteger, nullable=False, comment="设计人ID")
    designer_name = Column(String(50), nullable=False, comment="设计人")
    reviewer_id = Column(BigInteger, nullable=True, comment="审核人ID")
    reviewer_name = Column(String(50), nullable=True, comment="审核人")
    review_time = Column(DateTime, nullable=True, comment="审核时间")
    publish_time = Column(DateTime, nullable=True, comment="发布时间")
    remark = Column(String(500), nullable=True, comment="备注")
    created_by = Column(BigInteger, nullable=False, comment="创建人ID")
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, comment="是否删除")

    # 关系
    items = relationship("BomItem", back_populates="bom_header")
    versions = relationship("BomVersion", back_populates="bom_header")

    __table_args__ = (
        Index("idx_bom_project", "project_id"),
        Index("idx_bom_status", "status"),
    )


class BomItem(Base):
    """BOM明细表"""
    __tablename__ = "bom_item"

    item_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="明细ID")
    bom_id = Column(BigInteger, ForeignKey("bom_header.bom_id"), nullable=False, comment="BOM ID")
    project_id = Column(BigInteger, nullable=False, comment="项目ID")
    line_no = Column(Integer, nullable=False, comment="行号")
    material_id = Column(BigInteger, nullable=True, comment="物料ID")
    material_code = Column(String(30), nullable=False, comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")
    specification = Column(String(200), nullable=True, comment="规格型号")
    brand = Column(String(50), nullable=True, comment="品牌")
    category = Column(String(30), nullable=False, comment="物料类别")
    category_name = Column(String(50), nullable=True, comment="类别名称")
    unit = Column(String(20), default="pcs", comment="单位")
    quantity = Column(Numeric(10, 2), nullable=False, comment="需求数量")
    unit_price = Column(Numeric(12, 2), nullable=True, comment="单价")
    amount = Column(Numeric(12, 2), nullable=True, comment="金额")
    supplier_id = Column(BigInteger, nullable=True, comment="供应商ID")
    supplier_name = Column(String(100), nullable=True, comment="供应商名称")
    lead_time = Column(Integer, nullable=True, comment="采购周期(天)")
    is_long_lead = Column(SmallInteger, default=0, comment="是否长周期")
    is_key_part = Column(SmallInteger, default=0, comment="是否关键件")
    required_date = Column(Date, nullable=True, comment="需求日期")
    ordered_qty = Column(Numeric(10, 2), default=0, comment="已下单数量")
    received_qty = Column(Numeric(10, 2), default=0, comment="已到货数量")
    stock_qty = Column(Numeric(10, 2), default=0, comment="库存可用")
    shortage_qty = Column(Numeric(10, 2), default=0, comment="缺料数量")
    procurement_status = Column(String(20), default="待采购", comment="采购状态")
    drawing_no = Column(String(50), nullable=True, comment="图纸号")
    position_no = Column(String(50), nullable=True, comment="位置号")
    remark = Column(String(500), nullable=True, comment="备注")
    version = Column(String(10), default="V1.0", comment="版本")
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, comment="是否删除")

    # 关系
    bom_header = relationship("BomHeader", back_populates="items")

    __table_args__ = (
        Index("idx_item_bom", "bom_id"),
        Index("idx_item_project", "project_id"),
        Index("idx_item_material", "material_id"),
        Index("idx_item_category", "category"),
    )


class BomVersion(Base):
    """BOM版本表"""
    __tablename__ = "bom_version"

    version_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="版本ID")
    bom_id = Column(BigInteger, ForeignKey("bom_header.bom_id"), nullable=False, comment="BOM ID")
    version = Column(String(10), nullable=False, comment="版本号")
    version_type = Column(String(20), nullable=False, comment="版本类型：初始/变更/修订")
    ecn_id = Column(BigInteger, nullable=True, comment="关联ECN ID")
    ecn_code = Column(String(30), nullable=True, comment="ECN编号")
    change_summary = Column(String(500), nullable=True, comment="变更摘要")
    total_items = Column(Integer, default=0, comment="物料总数")
    total_cost = Column(Numeric(14, 2), default=0, comment="版本成本")
    snapshot_data = Column(Text, nullable=True, comment="BOM快照JSON")
    published_by = Column(BigInteger, nullable=False, comment="发布人ID")
    published_name = Column(String(50), nullable=False, comment="发布人")
    published_time = Column(DateTime, default=datetime.now, comment="发布时间")
    remark = Column(String(500), nullable=True, comment="备注")

    # 关系
    bom_header = relationship("BomHeader", back_populates="versions")

    __table_args__ = (
        Index("idx_version_bom", "bom_id"),
        Index("idx_version_ecn", "ecn_id"),
    )


# 物料类别映射
CATEGORY_MAP = {
    "ME": "机械件",
    "EL": "电气件",
    "PN": "气动件",
    "ST": "标准件",
    "OT": "外协件",
    "TR": "贸易件",
}


def get_category_name(category: str) -> str:
    """获取类别名称"""
    return CATEGORY_MAP.get(category, category)
