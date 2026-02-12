# -*- coding: utf-8 -*-
"""
商务支持模块 - 发货订单模型
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


class DeliveryOrder(Base, TimestampMixin):
    """发货单表"""

    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_no = Column(String(50), unique=True, nullable=False, comment="送货单号")

    # 关联
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, comment="销售订单ID")
    order_no = Column(String(50), comment="销售订单号")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")

    # 发货信息
    delivery_date = Column(Date, comment="发货日期")
    delivery_type = Column(String(20), comment="发货方式：express/logistics/self_pickup/install")
    logistics_company = Column(String(100), comment="物流公司")
    tracking_no = Column(String(100), comment="物流单号")

    # 收货信息
    receiver_name = Column(String(50), comment="收货人")
    receiver_phone = Column(String(20), comment="收货电话")
    receiver_address = Column(String(500), comment="收货地址")

    # 金额
    delivery_amount = Column(Numeric(15, 2), comment="本次发货金额")

    # 审批
    approval_status = Column(String(20), default="pending", comment="审批状态：pending/approved/rejected")
    approval_comment = Column(Text, comment="审批意见")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    # 特殊审批（应收未收情况）
    special_approval = Column(Boolean, default=False, comment="是否特殊审批")
    special_approver_id = Column(Integer, ForeignKey("users.id"), comment="特殊审批人ID")
    special_approval_reason = Column(Text, comment="特殊审批原因")

    # 送货单状态
    delivery_status = Column(String(20), default="draft", comment="送货单状态：draft/approved/printed/shipped/received/returned")
    print_date = Column(DateTime, comment="打印时间")
    ship_date = Column(DateTime, comment="实际发货时间")
    receive_date = Column(Date, comment="客户签收日期")

    # 送货单回收
    return_status = Column(String(20), default="pending", comment="送货单回收状态：pending/received/lost")
    return_date = Column(Date, comment="回收日期")
    signed_delivery_file_id = Column(Integer, comment="签收送货单文件ID")

    remark = Column(Text, comment="备注")

    # 关系
    sales_order = relationship("SalesOrder", back_populates="delivery_orders")
    contract = relationship("Contract", foreign_keys=[contract_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    approver = relationship("User", foreign_keys=[approved_by])
    special_approver = relationship("User", foreign_keys=[special_approver_id])

    __table_args__ = (
        Index("idx_delivery_no", "delivery_no"),
        Index("idx_order", "order_id"),
        Index("idx_delivery_customer", "customer_id"),
        Index("idx_delivery_order_status", "delivery_status"),
        Index("idx_return_status", "return_status"),
    )

    def __repr__(self):
        return f"<DeliveryOrder {self.delivery_no}>"
