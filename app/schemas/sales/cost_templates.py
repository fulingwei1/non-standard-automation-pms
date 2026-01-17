# -*- coding: utf-8 -*-
"""
成本模板 Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuoteCostTemplateCreate(BaseModel):
    """创建成本模板"""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="模板名称")
    description: Optional[str] = Field(default=None, description="描述")
    category: Optional[str] = Field(default=None, description="分类")
    items: Optional[List[dict]] = Field(default=None, description="模板项")


class QuoteCostTemplateUpdate(BaseModel):
    """更新成本模板"""
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="模板名称")
    description: Optional[str] = Field(default=None, description="描述")
    category: Optional[str] = Field(default=None, description="分类")
    items: Optional[List[dict]] = Field(default=None, description="模板项")


class QuoteCostTemplateResponse(BaseModel):
    """成本模板响应"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    items: Optional[List[dict]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PurchaseMaterialCostCreate(BaseModel):
    """创建采购物料成本"""
    model_config = ConfigDict(populate_by_name=True)

    material_id: int = Field(description="物料ID")
    supplier_id: Optional[int] = Field(default=None, description="供应商ID")
    unit_price: Decimal = Field(description="单价")
    currency: str = Field(default="CNY", description="货币")


class PurchaseMaterialCostUpdate(BaseModel):
    """更新采购物料成本"""
    model_config = ConfigDict(populate_by_name=True)

    unit_price: Optional[Decimal] = Field(default=None, description="单价")
    currency: Optional[str] = Field(default=None, description="货币")


class PurchaseMaterialCostResponse(BaseModel):
    """采购物料成本响应"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    material_id: int
    supplier_id: Optional[int] = None
    unit_price: Decimal
    currency: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaterialCostMatchRequest(BaseModel):
    """物料成本匹配请求"""
    model_config = ConfigDict(populate_by_name=True)

    material_ids: List[int] = Field(description="物料ID列表")


class MaterialCostMatchResponse(BaseModel):
    """物料成本匹配响应"""
    model_config = ConfigDict(populate_by_name=True)

    matched: List[dict] = Field(default_factory=list, description="匹配结果")
    unmatched: List[int] = Field(default_factory=list, description="未匹配的物料ID")


class MaterialCostUpdateReminderResponse(BaseModel):
    """物料成本更新提醒响应"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    material_id: int
    reminder_date: Optional[datetime] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class MaterialCostUpdateReminderUpdate(BaseModel):
    """更新物料成本更新提醒"""
    model_config = ConfigDict(populate_by_name=True)

    status: Optional[str] = Field(default=None, description="状态")
    reminder_date: Optional[datetime] = Field(default=None, description="提醒日期")
