# -*- coding: utf-8 -*-
"""
开票申请 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class InvoiceRequestCreate(BaseModel):
    """创建开票申请"""

    contract_id: int = Field(description="合同ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    payment_plan_id: Optional[int] = Field(default=None, description="关联回款计划ID")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_title: Optional[str] = Field(default=None, description="发票抬头")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    amount: Decimal = Field(description="不含税金额")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="含税金额")
    currency: Optional[str] = Field(default="CNY", description="币种")
    expected_issue_date: Optional[date] = Field(default=None, description="预计开票日期")
    expected_payment_date: Optional[date] = Field(default=None, description="预计回款日期")
    reason: Optional[str] = Field(default=None, description="开票事由")
    attachments: Optional[List[str]] = Field(default=None, description="附件列表")
    remark: Optional[str] = Field(default=None, description="备注")


class InvoiceRequestUpdate(BaseModel):
    """更新开票申请"""

    project_id: Optional[int] = None
    payment_plan_id: Optional[int] = None
    invoice_type: Optional[str] = None
    invoice_title: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_issue_date: Optional[date] = None
    expected_payment_date: Optional[date] = None
    reason: Optional[str] = None
    attachments: Optional[List[str]] = None
    remark: Optional[str] = None


class InvoiceRequestResponse(TimestampSchema):
    """开票申请响应"""

    id: int
    request_no: str
    contract_id: int
    contract_code: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    payment_plan_id: Optional[int] = None
    invoice_type: Optional[str] = None
    invoice_title: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_issue_date: Optional[date] = None
    expected_payment_date: Optional[date] = None
    reason: Optional[str] = None
    attachments: Optional[List[str]] = None
    remark: Optional[str] = None
    status: str
    approval_comment: Optional[str] = None
    requested_by: int
    requested_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    invoice_id: Optional[int] = None
    invoice_code: Optional[str] = None
    receipt_status: Optional[str] = None
    receipt_updated_at: Optional[datetime] = None


class InvoiceRequestApproveRequest(BaseModel):
    """审批开票申请"""

    approval_comment: Optional[str] = Field(default=None, description="审批意见")
    issue_date: Optional[date] = Field(default=None, description="实际开票日期")
    invoice_code: Optional[str] = Field(default=None, description="实际发票号")
    total_amount: Optional[Decimal] = Field(default=None, description="实际开票金额")


class InvoiceRequestRejectRequest(BaseModel):
    """驳回开票申请"""

    approval_comment: Optional[str] = Field(default=None, description="驳回原因")
