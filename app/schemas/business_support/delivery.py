# -*- coding: utf-8 -*-
"""
发货管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class DeliveryOrderItemCreate(BaseModel):
    """创建发货单明细"""

    sales_order_item_id: Optional[int] = Field(default=None, description="销售订单明细ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    item_name: Optional[str] = Field(default=None, max_length=200, description="明细名称")
    item_spec: Optional[str] = Field(default=None, max_length=200, description="规格型号")
    delivery_qty: Decimal = Field(gt=0, description="本次发货数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    unit_price: Optional[Decimal] = Field(default=None, description="单价")
    amount: Optional[Decimal] = Field(default=None, description="本次发货金额")
    remark: Optional[str] = Field(default=None, description="备注")


class DeliveryOrderItemResponse(TimestampSchema):
    """发货单明细响应"""

    id: int
    delivery_order_id: int
    sales_order_item_id: Optional[int] = None
    material_id: Optional[int] = None
    item_name: str
    item_spec: Optional[str] = None
    delivery_qty: Decimal
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    quality_status: Optional[str] = None
    remark: Optional[str] = None


class DeliveryOrderCreate(BaseModel):
    """创建发货单"""

    delivery_no: Optional[str] = Field(
        default=None, max_length=50, description="送货单号（不提供则自动生成）"
    )
    order_id: int = Field(description="销售订单ID")
    delivery_date: date = Field(description="计划发货日期")
    delivery_type: str = Field(max_length=20, description="发货方式")
    logistics_company: Optional[str] = Field(default=None, max_length=100, description="物流公司")
    tracking_no: Optional[str] = Field(default=None, max_length=100, description="物流单号")
    receiver_name: Optional[str] = Field(default=None, max_length=50, description="收货人")
    receiver_phone: Optional[str] = Field(default=None, max_length=20, description="收货电话")
    receiver_address: Optional[str] = Field(default=None, max_length=500, description="收货地址")
    delivery_amount: Decimal = Field(description="本次发货金额")
    items: Optional[List[DeliveryOrderItemCreate]] = Field(
        default_factory=list,
        description="发货明细；为空时从销售订单明细复制全部未发数量",
    )
    special_approval: Optional[bool] = Field(default=False, description="是否特殊审批")
    special_approval_reason: Optional[str] = Field(default=None, description="特殊审批原因")
    remark: Optional[str] = Field(default=None, description="备注")


class DeliveryOrderUpdate(BaseModel):
    """更新发货单"""

    delivery_date: Optional[date] = Field(default=None, description="计划发货日期")
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
    delivery_date: Optional[date] = Field(default=None, description="计划发货日期")
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
    ship_date: Optional[datetime] = Field(default=None, description="实际发货日期")
    receive_date: Optional[date] = None
    return_status: Optional[str] = None
    return_date: Optional[date] = None
    remark: Optional[str] = None
    items: List[DeliveryOrderItemResponse] = Field(default_factory=list, description="发货明细")


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
