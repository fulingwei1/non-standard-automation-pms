# -*- coding: utf-8 -*-
"""
标准成本库管理模块 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class StandardCostCreate(BaseModel):
    """创建标准成本"""
    cost_code: str = Field(..., max_length=50, description="成本项编码")
    cost_name: str = Field(..., max_length=200, description="成本项名称")
    cost_category: str = Field(..., description="成本类别：MATERIAL/LABOR/OVERHEAD")
    specification: Optional[str] = Field(None, max_length=500, description="规格型号")
    unit: str = Field(..., max_length=20, description="单位（如：件、kg、人天）")
    standard_cost: Decimal = Field(..., description="标准成本")
    currency: str = Field(default="CNY", max_length=10, description="币种")
    cost_source: str = Field(..., description="成本来源：HISTORICAL_AVG/INDUSTRY_STANDARD/EXPERT_ESTIMATE/VENDOR_QUOTE")
    source_description: Optional[str] = Field(None, description="来源说明")
    effective_date: date = Field(..., description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期（为空表示长期有效）")
    description: Optional[str] = Field(None, description="成本说明")
    notes: Optional[str] = Field(None, description="备注")


class StandardCostUpdate(BaseModel):
    """更新标准成本"""
    cost_name: Optional[str] = Field(None, max_length=200, description="成本项名称")
    cost_category: Optional[str] = Field(None, description="成本类别")
    specification: Optional[str] = Field(None, max_length=500, description="规格型号")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    standard_cost: Optional[Decimal] = Field(None, description="标准成本")
    currency: Optional[str] = Field(None, max_length=10, description="币种")
    cost_source: Optional[str] = Field(None, description="成本来源")
    source_description: Optional[str] = Field(None, description="来源说明")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    description: Optional[str] = Field(None, description="成本说明")
    notes: Optional[str] = Field(None, description="备注")


class StandardCostResponse(TimestampSchema):
    """标准成本响应"""
    id: int
    cost_code: str
    cost_name: str
    cost_category: str
    specification: Optional[str] = None
    unit: str
    standard_cost: Decimal
    currency: str
    cost_source: str
    source_description: Optional[str] = None
    effective_date: date
    expiry_date: Optional[date] = None
    version: int
    is_active: bool
    parent_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class StandardCostHistoryResponse(TimestampSchema):
    """标准成本历史记录响应"""
    id: int
    standard_cost_id: int
    change_type: str
    change_date: date
    old_cost: Optional[Decimal] = None
    new_cost: Optional[Decimal] = None
    old_effective_date: Optional[date] = None
    new_effective_date: Optional[date] = None
    change_reason: Optional[str] = None
    change_description: Optional[str] = None
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class StandardCostImportRow(BaseModel):
    """标准成本导入行数据"""
    cost_code: str = Field(..., description="成本项编码")
    cost_name: str = Field(..., description="成本项名称")
    cost_category: str = Field(..., description="成本类别")
    specification: Optional[str] = Field(None, description="规格型号")
    unit: str = Field(..., description="单位")
    standard_cost: Decimal = Field(..., description="标准成本")
    currency: str = Field(default="CNY", description="币种")
    cost_source: str = Field(..., description="成本来源")
    source_description: Optional[str] = Field(None, description="来源说明")
    effective_date: str = Field(..., description="生效日期(YYYY-MM-DD)")
    expiry_date: Optional[str] = Field(None, description="失效日期(YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="成本说明")
    notes: Optional[str] = Field(None, description="备注")


class StandardCostImportResult(BaseModel):
    """标准成本导入结果"""
    success_count: int = Field(..., description="成功导入数量")
    error_count: int = Field(..., description="失败数量")
    errors: List[dict] = Field(default=[], description="错误详情")
    warnings: List[dict] = Field(default=[], description="警告信息")


class StandardCostSearchRequest(BaseModel):
    """标准成本搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词（编码或名称）")
    cost_category: Optional[str] = Field(None, description="成本类别筛选")
    cost_source: Optional[str] = Field(None, description="成本来源筛选")
    is_active: Optional[bool] = Field(None, description="是否有效")
    effective_date_from: Optional[date] = Field(None, description="生效日期起")
    effective_date_to: Optional[date] = Field(None, description="生效日期止")


class ProjectCostComparisonRequest(BaseModel):
    """项目成本对比请求"""
    project_id: int = Field(..., description="项目ID")
    comparison_date: Optional[date] = Field(None, description="对比日期（默认当前日期）")


class ProjectCostComparisonItem(BaseModel):
    """项目成本对比项"""
    cost_code: str
    cost_name: str
    cost_category: str
    unit: str
    standard_cost: Decimal
    actual_cost: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    standard_total: Decimal
    actual_total: Optional[Decimal] = None
    variance: Optional[Decimal] = None  # 差异
    variance_rate: Optional[Decimal] = None  # 差异率（%）


class ProjectCostComparisonResponse(BaseModel):
    """项目成本对比响应"""
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    comparison_date: date
    items: List[ProjectCostComparisonItem]
    total_standard_cost: Decimal
    total_actual_cost: Decimal
    total_variance: Decimal
    total_variance_rate: Decimal


class ApplyStandardCostRequest(BaseModel):
    """应用标准成本到项目预算请求"""
    project_id: int = Field(..., description="项目ID")
    cost_items: List[dict] = Field(..., description="成本项列表 [{cost_code, quantity}]")
    budget_name: str = Field(..., description="预算名称")
    effective_date: Optional[date] = Field(None, description="预算生效日期")
    notes: Optional[str] = Field(None, description="备注")


class ApplyStandardCostResponse(BaseModel):
    """应用标准成本响应"""
    budget_id: int
    budget_no: str
    project_id: int
    total_amount: Decimal
    applied_items_count: int
    message: str
