# -*- coding: utf-8 -*-
"""
商务支持模块 - 对账模型
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Reconciliation(Base, TimestampMixin):
    """客户对账单表"""

    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reconciliation_no = Column(String(50), unique=True, nullable=False, comment="对账单号")

    # 客户
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    # 对账期间
    period_start = Column(Date, comment="对账开始日期")
    period_end = Column(Date, comment="对账结束日期")

    # 金额汇总
    opening_balance = Column(Numeric(15, 2), default=0, comment="期初余额")
    period_sales = Column(Numeric(15, 2), default=0, comment="本期销售")
    period_receipt = Column(Numeric(15, 2), default=0, comment="本期回款")
    closing_balance = Column(Numeric(15, 2), default=0, comment="期末余额")

    # 状态
    status = Column(String(20), default="draft", comment="状态：draft/sent/confirmed/disputed")
    sent_date = Column(Date, comment="发送日期")
    confirm_date = Column(Date, comment="确认日期")

    # 客户确认
    customer_confirmed = Column(Boolean, default=False, comment="客户是否确认")
    customer_confirm_date = Column(Date, comment="客户确认日期")
    customer_difference = Column(Numeric(15, 2), comment="客户差异金额")
    difference_reason = Column(Text, comment="差异原因")

    # 文件
    reconciliation_file_id = Column(Integer, comment="对账单文件ID")
    confirmed_file_id = Column(Integer, comment="确认回执文件ID")

    remark = Column(Text, comment="备注")

    # 关系
    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_reconciliation_no", "reconciliation_no"),
        Index("idx_customer_reconciliation", "customer_id"),
        Index("idx_period", "period_start", "period_end"),
        Index("idx_reconciliation_status", "status"),
    )

    def __repr__(self):
        return f"<Reconciliation {self.reconciliation_no}>"
