# -*- coding: utf-8 -*-
"""
客户标签模型
"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CustomerTag(Base, TimestampMixin):
    """客户标签表"""

    __tablename__ = "customer_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联客户
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, comment="客户ID")
    
    # 标签名称
    tag_name = Column(String(50), nullable=False, comment="标签名称")
    
    # 关系
    customer = relationship("Customer", back_populates="tags")
    
    # 索引
    __table_args__ = (
        Index("idx_customer_tag_customer", "customer_id"),
        Index("idx_customer_tag_name", "tag_name"),
        # 联合唯一索引：同一客户不能有重复标签
        Index("idx_customer_tag_unique", "customer_id", "tag_name", unique=True),
    )

    def __repr__(self):
        return f"<CustomerTag {self.tag_name} for customer {self.customer_id}>"


# 预定义标签常量
class PredefinedTags:
    """预定义标签"""
    KEY_CUSTOMER = "重点客户"
    STRATEGIC_CUSTOMER = "战略客户"
    NORMAL_CUSTOMER = "普通客户"
    LOST_CUSTOMER = "流失客户"
    HIGH_VALUE = "高价值客户"
    LONG_TERM = "长期合作"
    NEW_CUSTOMER = "新客户"
    
    @classmethod
    def all_tags(cls):
        """返回所有预定义标签"""
        return [
            cls.KEY_CUSTOMER,
            cls.STRATEGIC_CUSTOMER,
            cls.NORMAL_CUSTOMER,
            cls.LOST_CUSTOMER,
            cls.HIGH_VALUE,
            cls.LONG_TERM,
            cls.NEW_CUSTOMER,
        ]
