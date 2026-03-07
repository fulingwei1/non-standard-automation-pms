# -*- coding: utf-8 -*-
"""
成本模板 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuoteCostTemplateCreate(BaseModel):
    """创建成本模板"""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="模板名称")
    description: Optional[str] = Field(default=None, description="描述")
    category: Optional[str] = Field(default=None, description="分类")
    items: Optional[List[dict]] = Field(default=None, description="模板项")
    template_code: Optional[str] = Field(default=None, description="模板编码")
    template_name: Optional[str] = Field(default=None, description="模板名称（兼容字段）")
    template_type: Optional[str] = Field(default=None, description="模板类型")
    equipment_type: Optional[str] = Field(default=None, description="设备类型")
    industry: Optional[str] = Field(default=None, description="行业")
    cost_structure: Optional[Dict[str, Any]] = Field(default=None, description="成本结构")
    is_active: Optional[bool] = Field(default=True, description="是否启用")

    @model_validator(mode="before")
    @classmethod
    def _normalize_create_fields(cls, values):
        if not isinstance(values, dict):
            return values
        data = dict(values)
        if not data.get("name") and data.get("template_name"):
            data["name"] = data["template_name"]
        if data.get("cost_structure") is None and data.get("items") is not None:
            data["cost_structure"] = {"items": data.get("items")}
        if data.get("template_type") is None and data.get("category"):
            data["template_type"] = data.get("category")
        return data


class QuoteCostTemplateUpdate(BaseModel):
    """更新成本模板"""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="模板名称")
    description: Optional[str] = Field(default=None, description="描述")
    category: Optional[str] = Field(default=None, description="分类")
    items: Optional[List[dict]] = Field(default=None, description="模板项")
    template_code: Optional[str] = Field(default=None, description="模板编码")
    template_name: Optional[str] = Field(default=None, description="模板名称（兼容字段）")
    template_type: Optional[str] = Field(default=None, description="模板类型")
    equipment_type: Optional[str] = Field(default=None, description="设备类型")
    industry: Optional[str] = Field(default=None, description="行业")
    cost_structure: Optional[Dict[str, Any]] = Field(default=None, description="成本结构")
    is_active: Optional[bool] = Field(default=None, description="是否启用")

    @model_validator(mode="before")
    @classmethod
    def _normalize_update_fields(cls, values):
        if not isinstance(values, dict):
            return values
        data = dict(values)
        if not data.get("name") and data.get("template_name"):
            data["name"] = data["template_name"]
        if data.get("cost_structure") is None and data.get("items") is not None:
            data["cost_structure"] = {"items": data.get("items")}
        if data.get("template_type") is None and data.get("category"):
            data["template_type"] = data.get("category")
        return data


class QuoteCostTemplateResponse(BaseModel):
    """成本模板响应"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: Optional[str] = None
    template_code: Optional[str] = None
    template_name: Optional[str] = None
    template_type: Optional[str] = None
    equipment_type: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    items: Optional[List[dict]] = None
    cost_structure: Optional[Dict[str, Any]] = None
    total_cost: Optional[Decimal] = None
    is_active: Optional[bool] = True
    usage_count: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_compat_fields(cls, values):
        if not isinstance(values, dict):
            return values
        data = dict(values)

        if not data.get("name") and data.get("template_name"):
            data["name"] = data["template_name"]
        if not data.get("template_name") and data.get("name"):
            data["template_name"] = data["name"]

        if not data.get("category") and data.get("template_type"):
            data["category"] = data["template_type"]

        if data.get("items") is None and isinstance(data.get("cost_structure"), dict):
            structure = data["cost_structure"]
            if isinstance(structure.get("items"), list):
                data["items"] = structure.get("items")
            elif isinstance(structure.get("categories"), list):
                data["items"] = structure.get("categories")

        if data.get("cost_structure") is None and isinstance(data.get("items"), list):
            data["cost_structure"] = {"items": data["items"]}

        return data


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

    id: Optional[int] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    material_type: Optional[str] = None
    is_standard_part: Optional[bool] = None
    unit_cost: Optional[Decimal] = None
    currency: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_order_no: Optional[str] = None
    purchase_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None
    match_priority: Optional[int] = None
    match_keywords: Optional[str] = None
    usage_count: Optional[int] = None
    last_used_at: Optional[datetime] = None
    remark: Optional[str] = None
    submitted_by: Optional[int] = None
    submitter_name: Optional[str] = None
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


class CostMatchSuggestion(BaseModel):
    """成本匹配建议"""

    model_config = ConfigDict(populate_by_name=True)

    item_id: Optional[int] = Field(default=None, description="报价项ID")
    item_name: str = Field(description="物料名称")
    current_cost: Optional[Decimal] = Field(default=None, description="当前成本")
    suggested_cost: Optional[Decimal] = Field(default=None, description="建议成本")
    match_score: Optional[int] = Field(default=None, description="匹配分数")
    suggested_specification: Optional[str] = Field(default=None, description="建议规格")
    suggested_unit: Optional[str] = Field(default=None, description="建议单位")
    suggested_lead_time_days: Optional[int] = Field(default=None, description="建议交期(天)")
    suggested_cost_category: Optional[str] = Field(default=None, description="建议成本分类")
    reason: Optional[str] = Field(default=None, description="匹配原因")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    matched_cost_record: Optional[PurchaseMaterialCostResponse] = Field(
        default=None, description="匹配的成本记录"
    )
