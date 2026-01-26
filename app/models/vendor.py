# -*- coding: utf-8 -*-
"""
供应商统一模型 - 合并 suppliers 和 outsourcing_vendors

此模型整合了原来的物料供应商(suppliers)和外协商(outsourcing_vendors)，
通过 vendor_type 字段区分供应商类型。
"""

from sqlalchemy import Column, ForeignKey, Index, JSON, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, VendorBaseMixin


class Vendor(Base, TimestampMixin, VendorBaseMixin):
    """
    统一供应商表

    合并了原来的：
    - suppliers (物料供应商)
    - outsourcing_vendors (外协商)

    通过 vendor_type 区分：
    - MATERIAL: 物料供应商
    - OUTSOURCING: 外协商
    """

    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 覆盖 VendorBaseMixin 中的字段，添加 unique 约束
    supplier_code = Column(
        String(50), unique=True, nullable=False, comment="供应商编码"
    )
    supplier_name = Column(String(200), nullable=False, comment="供应商名称")

    # 供应商类型 - 区分物料供应商和外协商
    vendor_type = Column(
        String(20), nullable=False, comment="供应商类型: MATERIAL/OUTSOURCING"
    )

    # 资质信息
    business_license = Column(String(100), comment="营业执照号")
    qualification = Column(Text, comment="资质认证JSON")

    # 外协商特有字段（使用 JSON 存储灵活的加工能力信息）
    capabilities = Column(JSON, comment="加工能力（外协商专用）")

    # 物料供应商特有字段
    supplier_level = Column(String(1), default="B", comment="供应商等级")
    payment_terms = Column(String(50), comment="付款条款")

    remark = Column(Text, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系 - 统一关联
    # 物料关联
    materials = relationship(
        "MaterialSupplier", back_populates="vendor", lazy="dynamic"
    )
    # 采购订单关联（物料供应商）
    purchase_orders = relationship(
        "PurchaseOrder", back_populates="vendor", lazy="dynamic"
    )
    # 外协订单关联（外协商）
    outsourcing_orders = relationship(
        "OutsourcingOrder", back_populates="vendor", lazy="dynamic"
    )
    # 外协评价关联
    outsourcing_evaluations = relationship(
        "OutsourcingEvaluation", back_populates="vendor", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_vendor_type", "vendor_type"),
        Index("idx_vendor_status", "status"),
        Index("idx_vendor_level", "supplier_level"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self):
        return f"<Vendor {self.supplier_code} ({self.vendor_type})>"

    @property
    def is_material_vendor(self) -> bool:
        """是否为物料供应商"""
        return self.vendor_type == "MATERIAL"

    @property
    def is_outsourcing_vendor(self) -> bool:
        """是否为外协商"""
        return self.vendor_type == "OUTSOURCING"
