# -*- coding: utf-8 -*-
"""
商务支持模块 - 开票申请模型
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class InvoiceRequest(Base, TimestampMixin):
    """开票申请表"""

    __tablename__ = "invoice_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_no = Column(String(50), unique=True, nullable=False, comment="申请编号")

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    project_name = Column(String(200), comment="项目名称")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    payment_plan_id = Column(Integer, ForeignKey("project_payment_plans.id"), comment="关联回款计划ID")

    invoice_type = Column(String(20), comment="发票类型")
    invoice_title = Column(String(200), comment="发票抬头")
    tax_rate = Column(Numeric(5, 2), comment="税率(%)")
    amount = Column(Numeric(14, 2), nullable=False, comment="不含税金额")
    tax_amount = Column(Numeric(14, 2), comment="税额")
    total_amount = Column(Numeric(14, 2), comment="含税金额")
    currency = Column(String(10), default="CNY", comment="币种")
    expected_issue_date = Column(Date, comment="预计开票日期")
    expected_payment_date = Column(Date, comment="预计回款日期")

    reason = Column(Text, comment="开票事由")
    attachments = Column(Text, comment="附件列表JSON")
    remark = Column(Text, comment="备注")

    status = Column(String(20), default="PENDING", comment="状态：DRAFT/PENDING/APPROVED/REJECTED/CANCELLED")
    approval_comment = Column(Text, comment="审批意见")
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    requested_by_name = Column(String(50), comment="申请人姓名")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    invoice_id = Column(Integer, ForeignKey("invoices.id"), comment="生成的发票ID")
    receipt_status = Column(String(20), default="UNPAID", comment="回款状态：UNPAID/PARTIAL/PAID")
    receipt_updated_at = Column(DateTime, comment="回款状态更新时间")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    payment_plan = relationship("ProjectPaymentPlan", back_populates="invoice_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])

    __table_args__ = (
        Index("idx_invoice_request_no", "request_no"),
        Index("idx_invoice_request_contract", "contract_id"),
        Index("idx_invoice_request_project", "project_id"),
        Index("idx_invoice_request_customer", "customer_id"),
        Index("idx_invoice_request_status", "status"),
        Index("idx_invoice_request_plan", "payment_plan_id"),
    )

    def __repr__(self):
        return f"<InvoiceRequest {self.request_no}>"
