# -*- coding: utf-8 -*-
"""
商务支持模块 - 客户供应商注册模型
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CustomerSupplierRegistration(Base, TimestampMixin):
    """客户供应商入驻管理表"""

    __tablename__ = "customer_supplier_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_no = Column(String(100), unique=True, nullable=False, comment="入驻编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    platform_name = Column(String(100), nullable=False, comment="平台名称")
    platform_url = Column(String(500), comment="平台链接")

    registration_status = Column(String(20), default="PENDING", comment="状态：PENDING/SUBMITTED/APPROVED/REJECTED/ACTIVE")
    application_date = Column(Date, comment="申请日期")
    approved_date = Column(Date, comment="批准日期")
    expire_date = Column(Date, comment="有效期")

    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(30), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")

    required_docs = Column(Text, comment="提交资料JSON")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    review_comment = Column(Text, comment="审核意见")

    external_sync_status = Column(String(20), default="pending", comment="外部平台同步状态")
    last_sync_at = Column(DateTime, comment="最后同步时间")
    sync_message = Column(Text, comment="同步结果消息")

    remark = Column(Text, comment="备注")

    customer = relationship("Customer", foreign_keys=[customer_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_supplier_reg_customer", "customer_id"),
        Index("idx_supplier_reg_platform", "platform_name"),
        Index("idx_supplier_reg_status", "registration_status"),
    )

    def __repr__(self):
        return f"<CustomerSupplierRegistration {self.registration_no}>"
