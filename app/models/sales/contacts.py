# -*- coding: utf-8 -*-
"""
联系人模型
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    """联系人表"""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联客户
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, comment="所属客户ID")
    
    # 基础信息
    name = Column(String(100), nullable=False, comment="姓名")
    position = Column(String(100), comment="职位")
    department = Column(String(100), comment="部门")
    
    # 联系方式
    mobile = Column(String(20), comment="手机号码")
    phone = Column(String(20), comment="座机")
    email = Column(String(100), comment="电子邮箱")
    wechat = Column(String(100), comment="微信号")
    
    # 其他信息
    birthday = Column(Date, comment="生日")
    hobbies = Column(Text, comment="兴趣爱好")
    notes = Column(Text, comment="备注")
    
    # 主要联系人标记
    is_primary = Column(Boolean, default=False, comment="是否为主要联系人")
    
    # 关系
    customer = relationship("Customer", back_populates="contacts")
    
    # 索引
    __table_args__ = (
        Index("idx_contact_customer", "customer_id"),
        Index("idx_contact_primary", "is_primary"),
        Index("idx_contact_mobile", "mobile"),
        Index("idx_contact_email", "email"),
    )

    def __repr__(self):
        return f"<Contact {self.name} - {self.customer_id}>"
