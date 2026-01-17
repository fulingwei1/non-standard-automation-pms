# -*- coding: utf-8 -*-
"""
商务支持模块 - 回款跟踪模型
"""
from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PaymentReminder(Base, TimestampMixin):
    """回款催收记录表"""

    __tablename__ = "payment_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    payment_node = Column(String(50), comment="付款节点：prepayment/delivery/acceptance/warranty")
    payment_amount = Column(Numeric(15, 2), comment="应回款金额")
    plan_date = Column(Date, comment="计划回款日期")
    reminder_type = Column(String(20), comment="催收类型：call/email/visit/other")
    reminder_content = Column(Text, comment="催收内容")
    reminder_date = Column(Date, comment="催收日期")
    reminder_person_id = Column(Integer, ForeignKey("users.id"), comment="催收人ID")
    customer_response = Column(Text, comment="客户反馈")
    next_reminder_date = Column(Date, comment="下次催收日期")
    status = Column(String(20), default="pending", comment="状态：pending/completed/cancelled")
    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    project = relationship("Project", foreign_keys=[project_id])
    reminder_person = relationship("User", foreign_keys=[reminder_person_id])

    __table_args__ = (
        Index("idx_payment_reminder_contract", "contract_id"),
        Index("idx_payment_reminder_project", "project_id"),
        Index("idx_reminder_date", "reminder_date"),
    )

    def __repr__(self):
        return f"<PaymentReminder {self.id}>"
