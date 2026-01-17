# -*- coding: utf-8 -*-
"""
发票管理 Schema
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class InvoiceCreate(BaseModel):
    """创建发票"""
    model_config = {'populate_by_name': True}

    contract_id: int = Field(description="合同ID")
    invoice_code: Optional[str] = Field(default=None, max_length=20, description="发票编码")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_amount: Decimal = Field(gt=0, description="发票金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    invoice_date: Optional[date] = Field(default=None, description="开票日期")
    due_date: Optional[date] = Field(default=None, description="到期日期")
    remark: Optional[str] = Field(default=None, description="备注")
    amount: Optional[Decimal] = Field(default=None, description="金额（兼容字段）")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    status: Optional[str] = Field(default="DRAFT", description="发票状态")


class InvoiceUpdate(BaseModel):
    """更新发票"""

    invoice_code: Optional[str] = None
    invoice_type: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    remark: Optional[str] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


class InvoiceResponse(TimestampSchema):
    """发票响应"""

    id: int = Field(description="发票ID")
    contract_id: int = Field(description="合同ID")
    invoice_code: str = Field(description="发票编码")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_amount: Decimal = Field(description="发票金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    invoice_date: Optional[date] = Field(default=None, description="开票日期")
    due_date: Optional[date] = Field(default=None, description="到期日期")
    remark: Optional[str] = Field(default=None, description="备注")
    contract_code: Optional[str] = Field(default=None, description="合同编码")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    project_code: Optional[str] = Field(default=None, description="项目编码")
    project_name: Optional[str] = Field(default=None, description="项目名称")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    amount: Optional[Decimal] = Field(default=None, description="金额")
    paid_amount: Optional[Decimal] = Field(default=None, description="已付金额")
    paid_date: Optional[date] = Field(default=None, description="付款日期")
    payment_status: Optional[str] = Field(default=None, description="付款状态")
    status: str = Field(description="发票状态")
    issue_date: Optional[date] = Field(default=None, description="开票日期")


class InvoiceIssueRequest(BaseModel):
    """开票请求"""
    issue_date: date = Field(description="开票日期")


# 审批相关 Schema（多级审批 - 旧版）
class InvoiceApprovalCreate(BaseModel):
    """创建发票审批"""
    invoice_id: int = Field(description="发票ID")
    approval_level: int = Field(description="审批层级")
    approval_role: str = Field(description="审批角色")
    approver_id: Optional[int] = Field(default=None, description="审批人ID")
    due_date: Optional[date] = Field(default=None, description="到期日期")


class InvoiceApprovalResponse(TimestampSchema):
    """发票审批响应"""
    id: int = Field(description="审批ID")
    invoice_id: int = Field(description="发票ID")
    approval_level: int = Field(description="审批层级")
    approval_role: str = Field(description="审批角色")
    approver_id: Optional[int] = Field(default=None, description="审批人ID")
    approver_name: Optional[str] = Field(default=None, description="审批人姓名")
    approval_result: Optional[str] = Field(default=None, description="审批结果")
    approval_opinion: Optional[str] = Field(default=None, description="审批意见")
    status: str = Field(description="状态")
    approved_at: Optional[date] = Field(default=None, description="审批时间")
    due_date: Optional[date] = Field(default=None, description="到期日期")
    is_overdue: bool = Field(default=False, description="是否逾期")
