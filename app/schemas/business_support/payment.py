# -*- coding: utf-8 -*-
"""
回款催收 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class PaymentReminderCreate(BaseModel):
    """创建回款催收记录"""

    contract_id: int = Field(description="合同ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    payment_node: Optional[str] = Field(default=None, max_length=50, description="付款节点")
    payment_amount: Optional[Decimal] = Field(default=None, description="应回款金额")
    plan_date: Optional[date] = Field(default=None, description="计划回款日期")
    reminder_type: str = Field(max_length=20, description="催收类型")
    reminder_content: str = Field(description="催收内容")
    reminder_date: date = Field(description="催收日期")
    customer_response: Optional[str] = Field(default=None, description="客户反馈")
    next_reminder_date: Optional[date] = Field(default=None, description="下次催收日期")
    remark: Optional[str] = Field(default=None, description="备注")


class PaymentReminderUpdate(BaseModel):
    """更新回款催收记录"""

    reminder_type: Optional[str] = None
    reminder_content: Optional[str] = None
    reminder_date: Optional[date] = None
    customer_response: Optional[str] = None
    next_reminder_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class PaymentReminderResponse(TimestampSchema):
    """回款催收记录响应"""

    id: int
    contract_id: int
    project_id: Optional[int] = None
    payment_node: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    plan_date: Optional[date] = None
    reminder_type: Optional[str] = None
    reminder_content: Optional[str] = None
    reminder_date: Optional[date] = None
    reminder_person_id: Optional[int] = None
    customer_response: Optional[str] = None
    next_reminder_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None
