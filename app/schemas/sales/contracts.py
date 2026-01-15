# -*- coding: utf-8 -*-
"""
合同管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

from ..common import BaseSchema, TimestampSchema


class ContractDeliverableCreate(BaseModel):
    """创建合同交付物"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    deliverable_name: str = Field(max_length=200, description="交付物名称")
    deliverable_type: Optional[str] = Field(default=None, description="交付物类型")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    delivery_date: Optional[date] = Field(default=None, description="交付日期")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收标准")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractDeliverableResponse(TimestampSchema):
    """合同交付物响应"""

    id: int = Field(description="交付物ID")
    contract_id: int = Field(description="合同ID")
    deliverable_name: str = Field(description="交付物名称")
    deliverable_type: Optional[str] = Field(default=None, description="交付物类型")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    unit: Optional[str] = Field(default=None, description="单位")
    delivery_date: Optional[date] = Field(default=None, description="交付日期")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收标准")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractCreate(BaseModel):
    """创建合同"""

    model_config = ConfigDict(populate_by_name=True)

    contract_code: Optional[str] = Field(default=None, max_length=20, description="合同编码")
    quote_id: Optional[int] = Field(default=None, description="报价ID")
    customer_name: str = Field(max_length=100, description="客户名称")
    contract_name: str = Field(max_length=200, description="合同名称")
    contract_type: Optional[str] = Field(default=None, description="合同类型")
    currency: Optional[str] = Field(default="CNY", description="货币")
    exchange_rate: Optional[Decimal] = Field(default=1.0, description="汇率")
    contract_amount: Optional[Decimal] = Field(default=None, description="合同金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    signed_date: Optional[date] = Field(default=None, description="签订日期")
    start_date: Optional[date] = Field(default=None, description="生效日期")
    end_date: Optional[date] = Field(default=None, description="截止日期")
    delivery_terms: Optional[str] = Field(default=None, description="交货条款")
    payment_terms: Optional[str] = Field(default=None, description="付款条款")
    quality_terms: Optional[str] = Field(default=None, description="质量条款")
    warranty_terms: Optional[str] = Field(default=None, description="质保条款")
    other_terms: Optional[str] = Field(default=None, description="其他条款")
    remark: Optional[str] = Field(default=None, description="备注")
    deliverables: Optional[List[ContractDeliverableCreate]] = Field(default=None, description="交付物列表")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")


class ContractUpdate(BaseModel):
    """更新合同"""

    contract_code: Optional[str] = None
    customer_name: Optional[str] = None
    contract_name: Optional[str] = None
    contract_type: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    contract_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    quality_terms: Optional[str] = None
    warranty_terms: Optional[str] = None
    other_terms: Optional[str] = None
    remark: Optional[str] = None
    deliverables: Optional[List[ContractDeliverableCreate]] = None
    owner_id: Optional[int] = None


class ContractResponse(TimestampSchema):
    """合同响应"""

    id: int = Field(description="合同ID")
    contract_code: str = Field(description="合同编码")
    quote_id: Optional[int] = Field(default=None, description="报价ID")
    customer_name: str = Field(description="客户名称")
    contract_name: str = Field(description="合同名称")
    contract_type: Optional[str] = Field(default=None, description="合同类型")
    currency: Optional[str] = Field(default="CNY", description="货币")
    exchange_rate: Optional[Decimal] = Field(default=1.0, description="汇率")
    contract_amount: Optional[Decimal] = Field(default=None, description="合同金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    signed_date: Optional[date] = Field(default=None, description="签订日期")
    start_date: Optional[date] = Field(default=None, description="生效日期")
    end_date: Optional[date] = Field(default=None, description="截止日期")
    delivery_terms: Optional[str] = Field(default=None, description="交货条款")
    payment_terms: Optional[str] = Field(default=None, description="付款条款")
    quality_terms: Optional[str] = Field(default=None, description="质量条款")
    warranty_terms: Optional[str] = Field(default=None, description="质保条款")
    other_terms: Optional[str] = Field(default=None, description="其他条款")
    remark: Optional[str] = Field(default=None, description="备注")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")
    deliverables_count: Optional[int] = Field(default=None, description="交付物数量")
    quote_code: Optional[str] = Field(default=None, description="报价编码")
    status: Optional[str] = Field(default=None, description="状态")


class ContractAmendmentCreate(BaseModel):
    """创建合同变更"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    amendment_type: str = Field(description="变更类型")
    amendment_reason: str = Field(description="变更原因")
    amendment_content: str = Field(description="变更内容")
    amendment_amount: Optional[Decimal] = Field(default=None, description="变更金额")
    effective_date: Optional[date] = Field(default=None, description="生效日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractAmendmentResponse(TimestampSchema):
    """合同变更响应"""

    id: int = Field(description="变更ID")
    contract_id: int = Field(description="合同ID")
    amendment_type: str = Field(description="变更类型")
    amendment_reason: str = Field(description="变更原因")
    amendment_content: str = Field(description="变更内容")
    amendment_amount: Optional[Decimal] = Field(default=None, description="变更金额")
    effective_date: Optional[date] = Field(default=None, description="生效日期")
    remark: Optional[str] = Field(default=None, description="备注")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名")


class ContractSignRequest(BaseModel):
    """合同签订请求"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    sign_location: Optional[str] = Field(default=None, description="签订地点")
    sign_witness: Optional[str] = Field(default=None, description="见证人")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractProjectCreateRequest(BaseModel):
    """合同项目关联请求"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    project_id: int = Field(description="项目ID")
    allocation_amount: Optional[Decimal] = Field(default=None, description="分配金额")
    allocation_ratio: Optional[Decimal] = Field(default=None, description="分配比例")
    remark: Optional[str] = Field(default=None, description="备注")