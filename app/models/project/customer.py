# -*- coding: utf-8 -*-
"""
客户相关模型
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin
from .core import Project  # 导入 Project 以便在属性中使用


class Customer(Base, TimestampMixin):
    """
    客户表

    存储客户基本信息、联系方式、财务信息等
    """

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

    # 财务信息
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
    
    # 销售管理扩展字段
    website = Column(String(200), comment="公司网址")
    established_date = Column(String(20), comment="成立日期")  # 使用Date会更好，但为兼容性用String
    customer_level = Column(String(10), default="D", comment="客户等级：A/B/C/D")
    account_period = Column(Integer, default=30, comment="账期(天)")
    customer_source = Column(String(100), comment="客户来源")
    sales_owner_id = Column(Integer, ForeignKey("users.id"), comment="负责销售人员ID")
    last_follow_up_at = Column(String(30), comment="最后跟进时间")  # DateTime作为string存储
    annual_revenue = Column(Numeric(15, 2), default=0, comment="年成交额")
    cooperation_years = Column(Integer, default=0, comment="合作年限")

    # 关系
    projects = relationship("Project", back_populates="customer")
    sales_owner = relationship("User", foreign_keys=[sales_owner_id])
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    tags = relationship("CustomerTag", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="customer")

    # ========================================================================
    # 便捷属性方法
    # ========================================================================

    @property
    def display_name(self) -> str:
        """获取客户显示名称（优先使用简称）"""
        return self.short_name or self.customer_name

    @property
    def full_address(self) -> str:
        """获取完整地址"""
        parts = []
        if self.address:
            parts.append(self.address)
        return " ".join(parts) if parts else ""

    @property
    def contact_info(self) -> dict:
        """获取联系人信息"""
        return {
            'person': self.contact_person,
            'phone': self.contact_phone,
            'email': self.contact_email,
        }

    @property
    def bank_info(self) -> dict:
        """获取银行信息"""
        return {
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'tax_no': self.tax_no,
        }

    @property
    def is_vip(self) -> bool:
        """是否为VIP客户（信用等级A或以上）"""
        return self.credit_level in ['A', 'AA', 'AAA']

    @property
    def project_count(self) -> int:
        """获取项目数量"""
        return self.projects.count() if self.projects else 0

    @property
    def active_projects(self):
        """获取进行中的项目"""
        if not self.projects:
            return []
        return self.projects.filter(
            Project.stage.in_(['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8'])
        ).all()

    def update_level(self):
        """
        根据年成交额和合作年限自动更新客户等级
        
        规则：
        - A级：年成交额>100万，合作>3年
        - B级：年成交额50-100万，合作1-3年
        - C级：年成交额10-50万，合作<1年
        - D级：年成交额<10万或潜在客户
        """
        revenue = float(self.annual_revenue or 0)
        years = self.cooperation_years or 0
        
        if revenue > 1000000 and years > 3:
            self.customer_level = "A"
        elif revenue >= 500000 and years >= 1:
            self.customer_level = "B"
        elif revenue >= 100000:
            self.customer_level = "C"
        else:
            self.customer_level = "D"

    def __repr__(self):
        return f"<Customer {self.customer_code}>"
