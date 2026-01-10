# -*- coding: utf-8 -*-
"""
优势产品管理模型

管理公司优势产品（宣传册产品），用于：
1. 销售线索填写时优先选择
2. 中标率预测模型的产品因子计算
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class AdvantageProductCategory(Base, TimestampMixin):
    """优势产品类别

    如：白色家电、汽车电子、新能源、半导体、电动工具、自动化线体、其他设备、教育实训
    """

    __tablename__ = "advantage_product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="类别编码")
    name = Column(String(100), nullable=False, comment="类别名称")
    description = Column(Text, comment="类别描述")
    sort_order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    products = relationship("AdvantageProduct", back_populates="category", lazy="dynamic")

    __table_args__ = (
        Index("idx_adv_category_code", "code"),
        Index("idx_adv_category_active", "is_active"),
    )

    def __repr__(self):
        return f"<AdvantageProductCategory {self.code}: {self.name}>"


class AdvantageProduct(Base, TimestampMixin):
    """优势产品

    公司优势产品/宣传册产品，用于销售线索评估
    """

    __tablename__ = "advantage_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False, comment="产品编码（如KC2701）")
    product_name = Column(String(200), nullable=False, comment="产品名称")
    category_id = Column(Integer, ForeignKey("advantage_product_categories.id"), comment="所属类别")
    series_code = Column(String(50), comment="产品系列编码（如KC2700）")
    description = Column(Text, comment="产品描述")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    category = relationship("AdvantageProductCategory", back_populates="products")

    __table_args__ = (
        Index("idx_adv_product_code", "product_code"),
        Index("idx_adv_product_category", "category_id"),
        Index("idx_adv_product_series", "series_code"),
        Index("idx_adv_product_active", "is_active"),
    )

    def __repr__(self):
        return f"<AdvantageProduct {self.product_code}: {self.product_name}>"


# 默认类别配置（用于初始化）
DEFAULT_CATEGORIES = [
    {"code": "HOME_APPLIANCE", "name": "白色家电", "sort_order": 1},
    {"code": "AUTOMOTIVE", "name": "汽车电子", "sort_order": 2},
    {"code": "NEW_ENERGY", "name": "新能源", "sort_order": 3},
    {"code": "SEMICONDUCTOR", "name": "半导体", "sort_order": 4},
    {"code": "POWER_TOOL", "name": "电动工具", "sort_order": 5},
    {"code": "AUTOMATION_LINE", "name": "自动化线体", "sort_order": 6},
    {"code": "OTHER_EQUIPMENT", "name": "其他设备", "sort_order": 7},
    {"code": "EDUCATION", "name": "教育实训", "sort_order": 8},
]

# 类别名称到编码的映射（用于 Excel 导入）
CATEGORY_NAME_TO_CODE = {cat["name"]: cat["code"] for cat in DEFAULT_CATEGORIES}
