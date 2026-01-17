# -*- coding: utf-8 -*-
"""
客户相关模型
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """客户表"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), unique=True, nullable=False, comment="客户编码")
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    short_name = Column(String(50), comment="客户简称")
    customer_type = Column(String(20), comment="客户类型")
    industry = Column(String(50), comment="所属行业")
    scale = Column(String(20), comment="规模")
    address = Column(String(500), comment="详细地址")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")

    # NEW fields from DB
    legal_person = Column(String(50), comment="法人代表")
    tax_no = Column(String(50), comment="税号")
    bank_name = Column(String(100), comment="开户行")
    bank_account = Column(String(50), comment="账号")

    credit_level = Column(String(20), default="B", comment="信用等级")
    credit_limit = Column(Numeric(14, 2), comment="信用额度")
    payment_terms = Column(String(50), comment="付款条款")

    portal_enabled = Column(Boolean, default=False, comment="门户启用")
    portal_username = Column(String(100), comment="门户账号")

    status = Column(String(20), default="ACTIVE", comment="状态")
    remark = Column(Text, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    projects = relationship("Project", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.customer_code}>"
