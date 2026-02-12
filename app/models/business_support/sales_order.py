# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售订单模型
"""

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


class SalesOrder(Base, TimestampMixin):
    """销售订单表"""

    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单编号")

    # 关联
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    contract_no = Column(String(50), comment="合同编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    project_no = Column(String(50), comment="项目号")

    # 订单信息
    order_type = Column(String(20), default="standard", comment="订单类型：standard/sample/repair/other")
    order_amount = Column(Numeric(15, 2), comment="订单金额")
    currency = Column(String(10), default="CNY", comment="币种")

    # 交期
    required_date = Column(Date, comment="客户要求日期")
    promised_date = Column(Date, comment="承诺交期")

    # 状态
    order_status = Column(String(20), default="draft", comment="订单状态：draft/confirmed/in_production/ready/partial_shipped/shipped/completed/cancelled")

    # 项目号分配
    project_no_assigned = Column(Boolean, default=False, comment="是否已分配项目号")
    project_no_assigned_date = Column(DateTime, comment="项目号分配时间")
    project_notice_sent = Column(Boolean, default=False, comment="是否已发项目通知单")
    project_notice_date = Column(DateTime, comment="通知单发布时间")

    # ERP信息
    erp_order_no = Column(String(50), comment="ERP订单号")
    erp_sync_status = Column(String(20), default="pending", comment="ERP同步状态：pending/synced/failed")
    erp_sync_time = Column(DateTime, comment="ERP同步时间")

    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")

    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    delivery_orders = relationship("DeliveryOrder", back_populates="sales_order", cascade="all, delete-orphan")
    order_items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_order_no", "order_no"),
        Index("idx_sales_order_contract", "contract_id"),
        Index("idx_sales_order_customer", "customer_id"),
        Index("idx_sales_order_project", "project_id"),
        Index("idx_sales_order_status", "order_status"),
    )

    def __repr__(self):
        return f"<SalesOrder {self.order_no}>"


class SalesOrderItem(Base, TimestampMixin):
    """销售订单明细表"""

    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, comment="销售订单ID")
    item_name = Column(String(200), comment="明细名称")
    item_spec = Column(String(200), comment="规格型号")
    qty = Column(Numeric(10, 2), comment="数量")
    unit = Column(String(20), comment="单位")
    unit_price = Column(Numeric(12, 2), comment="单价")
    amount = Column(Numeric(12, 2), comment="金额")
    remark = Column(Text, comment="备注")

    # 关系
    sales_order = relationship("SalesOrder", back_populates="order_items")

    __table_args__ = (
        Index("idx_sales_order", "sales_order_id"),
    )

    def __repr__(self):
        return f"<SalesOrderItem {self.id}>"
