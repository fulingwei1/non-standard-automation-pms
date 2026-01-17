# -*- coding: utf-8 -*-
"""
客户对账单 Schema
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class ReconciliationCreate(BaseModel):
    """创建客户对账单"""

    customer_id: int = Field(description="客户ID")
    period_start: date = Field(description="对账开始日期")
    period_end: date = Field(description="对账结束日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ReconciliationUpdate(BaseModel):
    """更新客户对账单"""

    status: Optional[str] = None
    sent_date: Optional[date] = None
    customer_confirmed: Optional[bool] = None
    customer_confirm_date: Optional[date] = None
    customer_difference: Optional[Decimal] = None
    difference_reason: Optional[str] = None
    remark: Optional[str] = None


class ReconciliationResponse(TimestampSchema):
    """客户对账单响应"""

    id: int
    reconciliation_no: str
    customer_id: int
    customer_name: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    period_sales: Optional[Decimal] = None
    period_receipt: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    status: Optional[str] = None
    sent_date: Optional[date] = None
    confirm_date: Optional[date] = None
    customer_confirmed: Optional[bool] = None
    customer_confirm_date: Optional[date] = None
    customer_difference: Optional[Decimal] = None
    difference_reason: Optional[str] = None
    reconciliation_file_id: Optional[int] = None
    confirmed_file_id: Optional[int] = None
    remark: Optional[str] = None
