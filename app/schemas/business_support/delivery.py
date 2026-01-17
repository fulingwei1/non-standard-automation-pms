# -*- coding: utf-8 -*-
"""
发货管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class DeliveryOrderCreate(BaseModel):
    """创建发货单"""

    delivery_no: Optional[str] = Field(default=None, max_length=50, description="送货单号（不提供则自动生成）")
    order_id: int = Field(description="销售订单ID")
    delivery_date: date = Field(description="发货日期")
    delivery_type: str = Field(max_length=20, description="发货方式")
    logistics_company: Optional[str] = Field(default=None, max_length=100, description="物流公司")
    tracking_no: Optional[str] = Field(default=None, max_length=100, description="物流单号")
    receiver_name: Optional[str] = Field(default=None, max_length=50, description="收货人")
    receiver_phone: Optional[str] = Field(default=None, max_length=20, description="收货电话")
    receiver_address: Optional[str] = Field(default=None, max_length=500, description="收货地址")
    delivery_amount: Decimal = Field(description="本次发货金额")
    special_approval: Optional[bool] = Field(default=False, description="是否特殊审批")
    special_approval_reason: Optional[str] = Field(default=None, description="特殊审批原因")
    remark: Optional[str] = Field(default=None, description="备注")


class DeliveryOrderUpdate(BaseModel):
    """更新发货单"""

    delivery_date: Optional[date] = None
    delivery_type: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_amount: Optional[Decimal] = None
    delivery_status: Optional[str] = None
    remark: Optional[str] = None


class DeliveryOrderResponse(TimestampSchema):
    """发货单响应"""

    id: int
    delivery_no: str
    order_id: int
    order_no: Optional[str] = None
    contract_id: Optional[int] = None
    customer_id: int
    customer_name: Optional[str] = None
    project_id: Optional[int] = None
    delivery_date: Optional[date] = None
    delivery_type: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_amount: Optional[Decimal] = None
    approval_status: Optional[str] = None
    approval_comment: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    special_approval: Optional[bool] = None
    special_approver_id: Optional[int] = None
    special_approval_reason: Optional[str] = None
    delivery_status: Optional[str] = None
    print_date: Optional[datetime] = None
    ship_date: Optional[datetime] = None
    receive_date: Optional[date] = None
    return_status: Optional[str] = None
    return_date: Optional[date] = None
    remark: Optional[str] = None


class DeliveryApprovalRequest(BaseModel):
    """发货审批请求"""

    approved: bool = Field(description="是否审批通过")
    approval_comment: Optional[str] = Field(default=None, description="审批意见")


class DeliveryStatistics(BaseModel):
    """发货统计（给生产总监看）"""
    pending_shipments: int = 0
    shipped_today: int = 0
    in_transit: int = 0
    delivered_this_week: int = 0
    on_time_shipping_rate: float = 0.0
    avg_shipping_time: float = 0.0
    total_orders: int = 0
