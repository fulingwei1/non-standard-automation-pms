# -*- coding: utf-8 -*-
"""
销售机会管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

from ..common import BaseSchema, TimestampSchema


class OpportunityRequirementCreate(BaseModel):
    """创建机会需求"""

    model_config = ConfigDict(populate_by_name=True)

    opportunity_id: int = Field(description="机会ID")
    requirement_type: str = Field(description="需求类型")
    requirement_desc: str = Field(description="需求描述")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    priority: Optional[str] = Field(default="MEDIUM", description="优先级")
    expected_delivery_date: Optional[date] = Field(default=None, description="期望交付日期")
    budget: Optional[Decimal] = Field(default=None, description="预算")


class OpportunityRequirementResponse(TimestampSchema):
    """机会需求响应"""

    id: int = Field(description="需求ID")
    opportunity_id: int = Field(description="机会ID")
    requirement_type: str = Field(description="需求类型")
    requirement_desc: str = Field(description="需求描述")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    priority: Optional[str] = Field(default="MEDIUM", description="优先级")
    expected_delivery_date: Optional[date] = Field(default=None, description="期望交付日期")
    budget: Optional[Decimal] = Field(default=None, description="预算")


class OpportunityCreate(BaseModel):
    """创建销售机会"""

    model_config = ConfigDict(populate_by_name=True)

    opportunity_code: Optional[str] = Field(default=None, max_length=20, description="机会编码")
    lead_id: Optional[int] = Field(default=None, description="线索ID")
    customer_name: str = Field(max_length=100, description="客户名称")
    opportunity_name: str = Field(max_length=200, description="机会名称")
    opportunity_type: Optional[str] = Field(default=None, description="机会类型")
    industry: Optional[str] = Field(default=None, description="行业")
    product_category: Optional[str] = Field(default=None, description="产品类别")
    estimated_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    probability: Optional[int] = Field(default=None, ge=0, le=100, description="成交概率(%)")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    description: Optional[str] = Field(default=None, description="描述")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    status: Optional[str] = Field(default="NEW", description="状态")
    source: Optional[str] = Field(default=None, description="来源")
    requirements: Optional[List[OpportunityRequirementCreate]] = Field(default=None, description="需求列表")


class OpportunityUpdate(BaseModel):
    """更新销售机会"""

    opportunity_code: Optional[str] = None
    customer_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    opportunity_type: Optional[str] = None
    industry: Optional[str] = None
    product_category: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    source: Optional[str] = None
    requirements: Optional[List[OpportunityRequirementCreate]] = None


class OpportunityResponse(TimestampSchema):
    """销售机会响应"""

    id: int = Field(description="机会ID")
    opportunity_code: str = Field(description="机会编码")
    lead_id: Optional[int] = Field(default=None, description="线索ID")
    customer_name: str = Field(description="客户名称")
    opportunity_name: str = Field(description="机会名称")
    opportunity_type: Optional[str] = Field(default=None, description="机会类型")
    industry: Optional[str] = Field(default=None, description="行业")
    product_category: Optional[str] = Field(default=None, description="产品类别")
    estimated_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    probability: Optional[int] = Field(default=None, description="成交概率(%)")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    description: Optional[str] = Field(default=None, description="描述")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    status: str = Field(description="状态")
    source: Optional[str] = Field(default=None, description="来源")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")
    requirements_count: Optional[int] = Field(default=None, description="需求数量")
    lead_code: Optional[str] = Field(default=None, description="线索编码")