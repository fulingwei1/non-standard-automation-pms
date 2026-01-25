# -*- coding: utf-8 -*-
"""
发票相关模型
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from app.models.enums import DisputeStatusEnum, InvoiceStatusEnum, InvoiceTypeEnum


class Invoice(Base, TimestampMixin):
    """发票表"""
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_code = Column(String(30), unique=True, nullable=False, comment="发票编码")
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    payment_id = Column(Integer, ForeignKey("project_payment_plans.id"), comment="关联应收节点ID")
    invoice_type = Column(String(20), comment="发票类型")
    amount = Column(Numeric(14, 2), comment="金额")
    tax_rate = Column(Numeric(5, 2), comment="税率")
    tax_amount = Column(Numeric(14, 2), comment="税额")
    total_amount = Column(Numeric(14, 2), comment="含税总额")
    status = Column(String(20), default=InvoiceStatusEnum.DRAFT, comment="状态")
    payment_status = Column(String(20), comment="收款状态")
    issue_date = Column(Date, comment="开票日期")
    due_date = Column(Date, comment="到期日期")
    paid_amount = Column(Numeric(14, 2), default=0, comment="已收款金额")
    paid_date = Column(Date, comment="收款日期")
    buyer_name = Column(String(100), comment="购买方名称")
    buyer_tax_no = Column(String(30), comment="购买方税号")
    remark = Column(Text, comment="备注")

    contract = relationship("Contract", back_populates="invoices")
    project = relationship("Project", foreign_keys=[project_id])
    approvals = relationship("InvoiceApproval", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_code}>"


class ReceivableDispute(Base, TimestampMixin):
    """回款争议/卡点表"""
    __tablename__ = "receivable_disputes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("project_payment_plans.id"), nullable=False, comment="付款节点ID")
    reason_code = Column(String(30), comment="原因代码")
    description = Column(Text, comment="描述")
    status = Column(String(20), default=DisputeStatusEnum.OPEN, comment="状态")
    responsible_dept = Column(String(50), comment="责任部门")
    responsible_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    expect_resolve_date = Column(Date, comment="预期解决日期")

    responsible = relationship("User", foreign_keys=[responsible_id])

    def __repr__(self):
        return f"<ReceivableDispute {self.id}>"


class InvoiceApproval(Base, TimestampMixin):
    """发票审批表"""
    __tablename__ = "invoice_approvals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, comment="发票ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")
    approval_result = Column(String(20), comment="审批结果")
    approval_opinion = Column(Text, comment="审批意见")
    status = Column(String(20), default="PENDING", comment="状态")
    approved_at = Column(DateTime, comment="审批时间")
    due_date = Column(DateTime, comment="审批期限")
    is_overdue = Column(Boolean, default=False, comment="是否超期")

    invoice = relationship("Invoice", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_invoice_approval_invoice", "invoice_id"),
        Index("idx_invoice_approval_approver", "approver_id"),
        Index("idx_invoice_approval_status", "status"),
    )

    def __repr__(self):
        return f"<InvoiceApproval {self.invoice_id}-L{self.approval_level}>"
