# -*- coding: utf-8 -*-
"""
成本模板 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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
    """创建采购物料成本（与 PurchaseMaterialCost ORM 字段对齐）"""

    model_config = ConfigDict(populate_by_name=True)

    material_code: Optional[str] = Field(default=None, description="物料编码")
    material_name: str = Field(description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    brand: Optional[str] = Field(default=None, description="品牌")
    unit: Optional[str] = Field(default="件", description="单位")
    material_type: Optional[str] = Field(default=None, description="物料类型")
    is_standard_part: Optional[bool] = Field(default=True, description="是否标准件")
    unit_cost: Decimal = Field(
        description="单位成本",
        validation_alias=AliasChoices("unit_cost", "unit_price"),
    )
    currency: Optional[str] = Field(default="CNY", description="货币")
    supplier_id: Optional[int] = Field(default=None, description="供应商ID")
    supplier_name: Optional[str] = Field(default=None, description="供应商名称")
    purchase_date: Optional[date] = Field(default=None, description="采购日期")
    purchase_order_no: Optional[str] = Field(default=None, description="采购订单号")
    purchase_quantity: Optional[Decimal] = Field(default=None, description="采购数量")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    is_active: Optional[bool] = Field(default=True, description="是否启用")
    match_priority: Optional[int] = Field(default=0, description="匹配优先级")
    match_keywords: Optional[str] = Field(default=None, description="匹配关键词")
    remark: Optional[str] = Field(default=None, description="备注")


class PurchaseMaterialCostUpdate(BaseModel):
    """更新采购物料成本（与 PurchaseMaterialCost ORM 字段对齐）"""

    model_config = ConfigDict(populate_by_name=True)

    material_code: Optional[str] = Field(default=None, description="物料编码")
    material_name: Optional[str] = Field(default=None, description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    brand: Optional[str] = Field(default=None, description="品牌")
    unit: Optional[str] = Field(default=None, description="单位")
    material_type: Optional[str] = Field(default=None, description="物料类型")
    is_standard_part: Optional[bool] = Field(default=None, description="是否标准件")
    unit_cost: Optional[Decimal] = Field(
        default=None,
        description="单位成本",
        validation_alias=AliasChoices("unit_cost", "unit_price"),
    )
    currency: Optional[str] = Field(default=None, description="货币")
    supplier_id: Optional[int] = Field(default=None, description="供应商ID")
    supplier_name: Optional[str] = Field(default=None, description="供应商名称")
    purchase_date: Optional[date] = Field(default=None, description="采购日期")
    purchase_order_no: Optional[str] = Field(default=None, description="采购订单号")
    purchase_quantity: Optional[Decimal] = Field(default=None, description="采购数量")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    match_priority: Optional[int] = Field(default=None, description="匹配优先级")
    match_keywords: Optional[str] = Field(default=None, description="匹配关键词")
    remark: Optional[str] = Field(default=None, description="备注")


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
