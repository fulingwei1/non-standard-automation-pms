# -*- coding: utf-8 -*-
"""
报价管理 Schema
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..common import BaseSchema, TimestampSchema


class GateSubmitRequest(BaseModel):
    """提报请求"""

    model_config = ConfigDict(populate_by_name=True)

    opportunity_id: int = Field(description="机会ID")
    gate_type: str = Field(description="关口类型")
    submit_description: str = Field(description="提报描述")
    estimated_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")


class QuoteItemCreate(BaseModel):
    """创建报价项"""

    model_config = ConfigDict(populate_by_name=True)

    quote_id: int = Field(description="报价ID")
    product_code: Optional[str] = Field(default=None, max_length=50, description="产品编码")
    product_name: str = Field(max_length=200, description="产品名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    brand: Optional[str] = Field(default=None, max_length=100, description="品牌")
    quantity: Decimal = Field(gt=0, description="数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    unit_price: Optional[Decimal] = Field(default=None, ge=0, description="单价")
    discount_rate: Optional[Decimal] = Field(default=None, ge=0, le=100, description="折扣率(%)")
    discount_amount: Optional[Decimal] = Field(default=None, ge=0, description="折扣金额")
    total_amount: Optional[Decimal] = Field(default=None, ge=0, description="总金额")
    delivery_time: Optional[int] = Field(default=None, description="交货期(天)")
    warranty_period: Optional[int] = Field(default=None, description="质保期(月)")
    remark: Optional[str] = Field(default=None, description="备注")


class QuoteItemUpdate(BaseModel):
    """更新报价项"""

    product_code: Optional[str] = None
    product_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount_rate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    delivery_time: Optional[int] = None
    warranty_period: Optional[int] = None
    remark: Optional[str] = None


class QuoteItemBatchUpdate(BaseModel):
    """批量更新报价项"""

    items: List[QuoteItemUpdate] = Field(description="报价项列表")


class QuoteItemResponse(BaseSchema):
    """报价项响应"""

    id: int = Field(description="报价项ID")
    quote_id: int = Field(description="报价ID")
    product_code: Optional[str] = Field(default=None, description="产品编码")
    product_name: str = Field(description="产品名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    brand: Optional[str] = Field(default=None, description="品牌")
    quantity: Decimal = Field(description="数量")
    unit: Optional[str] = Field(default=None, description="单位")
    unit_price: Optional[Decimal] = Field(default=None, description="单价")
    discount_rate: Optional[Decimal] = Field(default=None, description="折扣率(%)")
    discount_amount: Optional[Decimal] = Field(default=None, description="折扣金额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    delivery_time: Optional[int] = Field(default=None, description="交货期(天)")
    warranty_period: Optional[int] = Field(default=None, description="质保期(月)")
    remark: Optional[str] = Field(default=None, description="备注")


class QuoteVersionCreate(BaseModel):
    """创建报价版本"""

    model_config = ConfigDict(populate_by_name=True)

    quote_id: int = Field(description="报价ID")
    version_no: str = Field(max_length=20, description="版本号")
    version_description: Optional[str] = Field(default=None, description="版本说明")
    total_amount: Decimal = Field(ge=0, description="总金额")
    valid_until: Optional[date] = Field(default=None, description="有效期至")
    terms: Optional[str] = Field(default=None, description="条款")
    remark: Optional[str] = Field(default=None, description="备注")


class QuoteVersionResponse(TimestampSchema):
    """报价版本响应"""

    id: int = Field(description="版本ID")
    quote_id: int = Field(description="报价ID")
    version_no: str = Field(description="版本号")
    version_description: Optional[str] = Field(default=None, description="版本说明")
    total_amount: Decimal = Field(description="总金额")
    valid_until: Optional[date] = Field(default=None, description="有效期至")
    terms: Optional[str] = Field(default=None, description="条款")
    remark: Optional[str] = Field(default=None, description="备注")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名")


class QuoteCreate(BaseModel):
    """创建报价"""

    model_config = ConfigDict(populate_by_name=True)

    quote_code: Optional[str] = Field(default=None, max_length=20, description="报价编码")
    opportunity_id: Optional[int] = Field(default=None, description="机会ID")
    customer_name: str = Field(max_length=100, description="客户名称")
    quote_name: str = Field(max_length=200, description="报价名称")
    quote_type: Optional[str] = Field(default=None, description="报价类型")
    currency: Optional[str] = Field(default="CNY", description="货币")
    exchange_rate: Optional[Decimal] = Field(default=1.0, description="汇率")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    valid_until: Optional[date] = Field(default=None, description="有效期至")
    delivery_terms: Optional[str] = Field(default=None, description="交货条款")
    payment_terms: Optional[str] = Field(default=None, description="付款条款")
    terms: Optional[str] = Field(default=None, description="商务条款")
    remark: Optional[str] = Field(default=None, description="备注")
    items: Optional[List[QuoteItemCreate]] = Field(default=None, description="报价项列表")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")


class QuoteUpdate(BaseModel):
    """更新报价"""

    quote_code: Optional[str] = None
    customer_name: Optional[str] = None
    quote_name: Optional[str] = None
    quote_type: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    valid_until: Optional[date] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    terms: Optional[str] = None
    remark: Optional[str] = None
    items: Optional[List[QuoteItemCreate]] = None
    owner_id: Optional[int] = None


class QuoteResponse(TimestampSchema):
    """报价响应"""

    id: int = Field(description="报价ID")
    quote_code: str = Field(description="报价编码")
    opportunity_id: Optional[int] = Field(default=None, description="机会ID")
    customer_name: str = Field(description="客户名称")
    quote_name: str = Field(description="报价名称")
    quote_type: Optional[str] = Field(default=None, description="报价类型")
    currency: Optional[str] = Field(default="CNY", description="货币")
    exchange_rate: Optional[Decimal] = Field(default=1.0, description="汇率")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    valid_until: Optional[date] = Field(default=None, description="有效期至")
    delivery_terms: Optional[str] = Field(default=None, description="交货条款")
    payment_terms: Optional[str] = Field(default=None, description="付款条款")
    terms: Optional[str] = Field(default=None, description="商务条款")
    remark: Optional[str] = Field(default=None, description="备注")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")
    items_count: Optional[int] = Field(default=None, description="报价项数量")
    opportunity_code: Optional[str] = Field(default=None, description="机会编码")
    status: Optional[str] = Field(default=None, description="状态")


class QuoteApproveRequest(BaseModel):
    """报价审批请求"""

    model_config = ConfigDict(populate_by_name=True)

    approve_action: str = Field(description="审批动作")
    approve_comment: Optional[str] = Field(default=None, description="审批意见")
    next_approver_id: Optional[int] = Field(default=None, description="下一审批人ID")
