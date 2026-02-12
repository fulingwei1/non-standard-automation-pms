# -*- coding: utf-8 -*-
"""
客户管理 Schema
包含客户相关的创建、更新、响应模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class CustomerCreate(BaseModel):
    """创建客户"""

    customer_code: Optional[str] = Field(default=None, max_length=50, description="客户编码（不提供则自动生成）")
    customer_name: str = Field(max_length=200, description="客户名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None


class CustomerUpdate(BaseModel):
    """更新客户"""

    customer_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_level: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class CustomerResponse(TimestampSchema):
    """客户响应"""

    id: int
    customer_code: str
    customer_name: str
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    credit_level: str = "B"
    credit_limit: Optional[Decimal] = None
    status: str = "ACTIVE"
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None

    class Config:
        from_attributes = True


class Customer360Summary(BaseModel):
    """客户360度概要"""

    total_projects: int = 0
    active_projects: int = 0
    pipeline_amount: Decimal = 0
    total_contract_amount: Decimal = 0
    open_receivables: Decimal = 0
    win_rate: float = 0
    avg_margin: Optional[Decimal] = None
    last_activity: Optional[datetime] = None


class Customer360ProjectItem(BaseModel):
    """客户项目摘要"""

    project_id: int
    project_code: str
    project_name: str
    stage: Optional[str] = None
    status: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    contract_amount: Optional[Decimal] = None
    planned_end_date: Optional[date] = None


class Customer360OpportunityItem(BaseModel):
    """客户商机摘要"""

    opportunity_id: int
    opp_code: str
    opp_name: str
    stage: str
    est_amount: Optional[Decimal] = None
    owner_name: Optional[str] = None
    win_probability: Optional[float] = None
    updated_at: Optional[datetime] = None


class Customer360QuoteItem(BaseModel):
    """客户报价摘要"""

    quote_id: int
    quote_code: str
    status: str
    total_price: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    owner_name: Optional[str] = None
    valid_until: Optional[date] = None


class Customer360ContractItem(BaseModel):
    """客户合同摘要"""

    contract_id: int
    contract_code: str
    status: str
    contract_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    project_code: Optional[str] = None


class Customer360InvoiceItem(BaseModel):
    """客户发票摘要"""

    invoice_id: int
    invoice_code: str
    status: str
    total_amount: Optional[Decimal] = None
    issue_date: Optional[date] = None
    paid_amount: Optional[Decimal] = None


class Customer360PaymentPlanItem(BaseModel):
    """客户收款节点"""

    plan_id: int
    project_id: Optional[int] = None
    payment_name: str
    status: str
    planned_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None


class Customer360CommunicationItem(BaseModel):
    """客户沟通记录摘要"""

    communication_id: int
    topic: str
    communication_type: Optional[str] = None
    communication_date: Optional[date] = None
    owner_name: Optional[str] = None
    follow_up_required: Optional[bool] = None


class Customer360Response(BaseModel):
    """客户360度视图响应"""

    basic_info: CustomerResponse
    summary: Customer360Summary
    projects: List[Customer360ProjectItem] = []
    opportunities: List[Customer360OpportunityItem] = []
    quotes: List[Customer360QuoteItem] = []
    contracts: List[Customer360ContractItem] = []
    invoices: List[Customer360InvoiceItem] = []
    payment_plans: List[Customer360PaymentPlanItem] = []
    communications: List[Customer360CommunicationItem] = []
