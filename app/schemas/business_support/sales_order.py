# -*- coding: utf-8 -*-
"""
销售订单管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class SalesOrderItemCreate(BaseModel):
    """创建销售订单明细"""

    item_name: str = Field(max_length=200, description="明细名称")
    item_spec: Optional[str] = Field(default=None, max_length=200, description="规格型号")
    qty: Decimal = Field(description="数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    unit_price: Decimal = Field(description="单价")
    amount: Decimal = Field(description="金额")
    remark: Optional[str] = Field(default=None, description="备注")


class SalesOrderItemResponse(TimestampSchema):
    """销售订单明细响应"""

    id: int
    sales_order_id: int
    item_name: Optional[str] = None
    item_spec: Optional[str] = None
    qty: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    remark: Optional[str] = None


class SalesOrderCreate(BaseModel):
    """创建销售订单"""

    order_no: Optional[str] = Field(default=None, max_length=50, description="订单编号（不提供则自动生成）")
    contract_id: Optional[int] = Field(default=None, description="合同ID")
    customer_id: int = Field(description="客户ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    order_type: Optional[str] = Field(default="standard", max_length=20, description="订单类型")
    order_amount: Decimal = Field(description="订单金额")
    currency: Optional[str] = Field(default="CNY", max_length=10, description="币种")
    required_date: Optional[date] = Field(default=None, description="客户要求日期")
    promised_date: Optional[date] = Field(default=None, description="承诺交期")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    sales_person_name: Optional[str] = Field(default=None, max_length=50, description="业务员")
    remark: Optional[str] = Field(default=None, description="备注")
    items: Optional[List[SalesOrderItemCreate]] = Field(default_factory=list, description="订单明细")


class SalesOrderUpdate(BaseModel):
    """更新销售订单"""

    order_type: Optional[str] = None
    order_amount: Optional[Decimal] = None
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    order_status: Optional[str] = None
    erp_order_no: Optional[str] = None
    remark: Optional[str] = None


class SalesOrderResponse(TimestampSchema):
    """销售订单响应"""

    id: int
    order_no: str
    contract_id: Optional[int] = None
    contract_no: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    project_id: Optional[int] = None
    project_no: Optional[str] = None
    order_type: Optional[str] = None
    order_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    order_status: Optional[str] = None
    project_no_assigned: Optional[bool] = None
    project_no_assigned_date: Optional[datetime] = None
    project_notice_sent: Optional[bool] = None
    project_notice_date: Optional[datetime] = None
    erp_order_no: Optional[str] = None
    erp_sync_status: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    remark: Optional[str] = None
    items: Optional[List[SalesOrderItemResponse]] = None


class AssignProjectRequest(BaseModel):
    """分配项目号请求"""

    project_id: int = Field(description="项目ID")
    project_no: Optional[str] = Field(default=None, max_length=50, description="项目号（不提供则使用项目编码）")


class SendNoticeRequest(BaseModel):
    """发送项目通知单请求"""

    notice_content: Optional[str] = Field(default=None, description="通知内容")
    recipients: Optional[List[int]] = Field(default_factory=list, description="接收人ID列表")
