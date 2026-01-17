# -*- coding: utf-8 -*-
"""
齐套分析模块 Pydantic Schemas

基于装配工艺路径的智能齐套分析系统
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ========== 装配阶段 ==========
class AssemblyStageBase(BaseModel):
    """装配阶段基础Schema"""
    stage_code: str = Field(..., max_length=20, description="阶段编码")
    stage_name: str = Field(..., max_length=50, description="阶段名称")
    stage_order: int = Field(..., ge=1, le=10, description="阶段顺序")
    default_duration: int = Field(default=8, ge=0, description="默认工期(小时)")
    color_code: str = Field(default="#1890ff", max_length=20, description="显示颜色")
    description: Optional[str] = Field(None, description="阶段描述")
    is_active: bool = Field(default=True, description="是否启用")


class AssemblyStageCreate(AssemblyStageBase):
    """创建装配阶段"""
    pass


class AssemblyStageUpdate(BaseModel):
    """更新装配阶段"""
    stage_name: Optional[str] = Field(None, max_length=50)
    default_duration: Optional[int] = Field(None, ge=0)
    color_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AssemblyStageResponse(AssemblyStageBase):
    """装配阶段响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 装配工艺模板 ==========
class AssemblyTemplateBase(BaseModel):
    """装配模板基础Schema"""
    template_code: str = Field(..., max_length=50, description="模板编码")
    template_name: str = Field(..., max_length=200, description="模板名称")
    equipment_type: Optional[str] = Field(None, max_length=50, description="设备类型")
    stage_config: Optional[Dict[str, Any]] = Field(None, description="阶段配置")
    is_default: bool = Field(default=False, description="是否默认模板")
    is_active: bool = Field(default=True, description="是否启用")


class AssemblyTemplateCreate(AssemblyTemplateBase):
    """创建装配模板"""
    pass


class AssemblyTemplateUpdate(BaseModel):
    """更新装配模板"""
    template_name: Optional[str] = Field(None, max_length=200)
    equipment_type: Optional[str] = Field(None, max_length=50)
    stage_config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AssemblyTemplateResponse(AssemblyTemplateBase):
    """装配模板响应"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 物料分类映射 ==========
class CategoryStageMappingBase(BaseModel):
    """物料分类映射基础Schema"""
    category_id: int = Field(..., description="物料分类ID")
    stage_code: str = Field(..., max_length=20, description="默认装配阶段")
    is_blocking: bool = Field(default=True, description="是否阻塞性物料")
    can_postpone: bool = Field(default=False, description="是否可后补")
    priority: int = Field(default=50, ge=0, le=100, description="优先级")


class CategoryStageMappingCreate(CategoryStageMappingBase):
    """创建物料分类映射"""
    pass


class CategoryStageMappingUpdate(BaseModel):
    """更新物料分类映射"""
    stage_code: Optional[str] = Field(None, max_length=20)
    is_blocking: Optional[bool] = None
    can_postpone: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)


class CategoryStageMappingResponse(CategoryStageMappingBase):
    """物料分类映射响应"""
    id: int
    category_name: Optional[str] = None  # 关联显示
    stage_name: Optional[str] = None  # 关联显示
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== BOM物料装配属性 ==========
class BomItemAssemblyAttrsBase(BaseModel):
    """BOM物料装配属性基础Schema"""
    bom_item_id: int = Field(..., description="BOM明细ID")
    bom_id: int = Field(..., description="BOM表头ID")
    assembly_stage: str = Field(..., max_length=20, description="装配阶段")
    importance_level: str = Field(default="NORMAL", max_length=20, description="重要程度")
    is_blocking: bool = Field(default=True, description="是否阻塞性")
    can_postpone: bool = Field(default=False, description="是否可后补")
    has_substitute: bool = Field(default=False, description="是否有替代料")
    substitute_material_id: Optional[int] = Field(None, description="替代物料ID")
    stage_order: int = Field(default=0, ge=0, description="阶段内排序")
    remark: Optional[str] = Field(None, description="备注")


class BomItemAssemblyAttrsCreate(BomItemAssemblyAttrsBase):
    """创建BOM物料装配属性"""
    pass


class BomItemAssemblyAttrsBatchCreate(BaseModel):
    """批量创建BOM物料装配属性"""
    items: List[BomItemAssemblyAttrsCreate] = Field(..., description="属性列表")


class BomItemAssemblyAttrsUpdate(BaseModel):
    """更新BOM物料装配属性"""
    assembly_stage: Optional[str] = Field(None, max_length=20)
    importance_level: Optional[str] = Field(None, max_length=20)
    is_blocking: Optional[bool] = None
    can_postpone: Optional[bool] = None
    has_substitute: Optional[bool] = None
    substitute_material_id: Optional[int] = None
    stage_order: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


class BomItemAssemblyAttrsResponse(BomItemAssemblyAttrsBase):
    """BOM物料装配属性响应"""
    id: int
    material_code: Optional[str] = None  # 关联显示
    material_name: Optional[str] = None  # 关联显示
    required_qty: Optional[Decimal] = None  # 关联显示
    stage_name: Optional[str] = None  # 关联显示
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BomAssemblyAttrsAutoRequest(BaseModel):
    """自动分配装配属性请求"""
    bom_id: int = Field(..., description="BOM ID")
    overwrite: bool = Field(default=False, description="是否覆盖已有配置")


class BomAssemblyAttrsTemplateRequest(BaseModel):
    """套用模板请求"""
    bom_id: int = Field(..., description="BOM ID")
    template_id: int = Field(..., description="模板ID")
    overwrite: bool = Field(default=False, description="是否覆盖已有配置")


# ========== 齐套分析结果 ==========
class StageKitRate(BaseModel):
    """阶段齐套率"""
    stage_code: str = Field(..., description="阶段编码")
    stage_name: str = Field(..., description="阶段名称")
    stage_order: int = Field(..., description="阶段顺序")
    total_items: int = Field(..., description="物料总项数")
    fulfilled_items: int = Field(..., description="已齐套项数")
    kit_rate: Decimal = Field(..., description="齐套率(%)")
    blocking_total: int = Field(..., description="阻塞性物料总数")
    blocking_fulfilled: int = Field(..., description="阻塞性齐套数")
    blocking_rate: Decimal = Field(..., description="阻塞齐套率(%)")
    can_start: bool = Field(..., description="是否可开始")
    color_code: str = Field(..., description="显示颜色")


class MaterialReadinessBase(BaseModel):
    """齐套分析结果基础Schema"""
    readiness_no: str = Field(..., max_length=50, description="分析单号")
    project_id: int = Field(..., description="项目ID")
    machine_id: Optional[int] = Field(None, description="机台ID")
    bom_id: int = Field(..., description="BOM ID")
    check_date: date = Field(..., description="检查日期")
    overall_kit_rate: Decimal = Field(..., description="整体齐套率(%)")
    blocking_kit_rate: Decimal = Field(..., description="阻塞性齐套率(%)")
    can_start: bool = Field(..., description="是否可开工")
    first_blocked_stage: Optional[str] = Field(None, description="首个阻塞阶段")
    estimated_ready_date: Optional[date] = Field(None, description="预计齐套日期")


class MaterialReadinessCreate(BaseModel):
    """创建齐套分析请求"""
    project_id: int = Field(..., description="项目ID")
    machine_id: Optional[int] = Field(None, description="机台ID")
    bom_id: int = Field(..., description="BOM ID")
    check_date: Optional[date] = Field(None, description="检查日期，默认今天")


class MaterialReadinessResponse(MaterialReadinessBase):
    """齐套分析结果响应"""
    id: int
    stage_kit_rates: List[StageKitRate] = Field(default_factory=list, description="各阶段齐套率")
    project_no: Optional[str] = None  # 关联显示
    project_name: Optional[str] = None  # 关联显示
    machine_no: Optional[str] = None  # 关联显示
    bom_no: Optional[str] = None  # 关联显示
    analysis_time: datetime
    analyzed_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialReadinessDetailResponse(MaterialReadinessResponse):
    """齐套分析详情响应(含缺料明细)"""
    shortage_details: List['ShortageDetailResponse'] = Field(default_factory=list, description="缺料明细")


# ========== 缺料明细 ==========
class ShortageDetailBase(BaseModel):
    """缺料明细基础Schema"""
    readiness_id: int = Field(..., description="齐套分析ID")
    bom_item_id: int = Field(..., description="BOM明细ID")
    material_id: int = Field(..., description="物料ID")
    material_code: str = Field(..., max_length=50, description="物料编码")
    material_name: str = Field(..., max_length=200, description="物料名称")
    assembly_stage: str = Field(..., max_length=20, description="装配阶段")
    is_blocking: bool = Field(default=True, description="是否阻塞性")
    required_qty: Decimal = Field(..., description="需求数量")
    stock_qty: Decimal = Field(default=0, description="库存数量")
    allocated_qty: Decimal = Field(default=0, description="已分配数量")
    in_transit_qty: Decimal = Field(default=0, description="在途数量")
    available_qty: Decimal = Field(..., description="可用数量")
    shortage_qty: Decimal = Field(..., description="缺料数量")
    shortage_rate: Decimal = Field(..., description="缺料比例(%)")
    expected_arrival_date: Optional[date] = Field(None, description="预计到货日期")
    alert_level: str = Field(default="L4", max_length=10, description="预警级别")


class ShortageDetailResponse(ShortageDetailBase):
    """缺料明细响应"""
    id: int
    stage_name: Optional[str] = None  # 关联显示
    importance_level: Optional[str] = None
    can_postpone: Optional[bool] = None
    has_substitute: Optional[bool] = None
    substitute_material_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 预警规则 ==========
class ShortageAlertRuleBase(BaseModel):
    """预警规则基础Schema"""
    rule_code: str = Field(..., max_length=50, description="规则编码")
    rule_name: str = Field(..., max_length=100, description="规则名称")
    alert_level: str = Field(..., max_length=10, description="预警级别(L1-L4)")
    days_before_required: int = Field(..., ge=0, description="距需求日期天数")
    only_blocking: bool = Field(default=False, description="仅阻塞性物料")
    min_shortage_rate: Decimal = Field(default=0, description="最小缺料比例(%)")
    response_deadline_hours: int = Field(default=24, ge=1, description="响应时限(小时)")
    notify_roles: Optional[List[str]] = Field(None, description="通知角色列表")
    is_active: bool = Field(default=True, description="是否启用")


class ShortageAlertRuleCreate(ShortageAlertRuleBase):
    """创建预警规则"""
    pass


class ShortageAlertRuleUpdate(BaseModel):
    """更新预警规则"""
    rule_name: Optional[str] = Field(None, max_length=100)
    days_before_required: Optional[int] = Field(None, ge=0)
    only_blocking: Optional[bool] = None
    min_shortage_rate: Optional[Decimal] = None
    response_deadline_hours: Optional[int] = Field(None, ge=1)
    notify_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ShortageAlertRuleResponse(ShortageAlertRuleBase):
    """预警规则响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 缺料预警 ==========
class ShortageAlertItem(BaseModel):
    """缺料预警项"""
    shortage_id: int = Field(..., description="缺料明细ID")
    readiness_id: int = Field(..., description="齐套分析ID")
    project_id: int = Field(..., description="项目ID")
    project_no: str = Field(..., description="项目编号")
    project_name: str = Field(..., description="项目名称")
    machine_id: Optional[int] = Field(None, description="机台ID")
    machine_no: Optional[str] = Field(None, description="机台编号")
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    assembly_stage: str = Field(..., description="装配阶段")
    stage_name: str = Field(..., description="阶段名称")
    is_blocking: bool = Field(..., description="是否阻塞性")
    required_qty: Decimal = Field(..., description="需求数量")
    shortage_qty: Decimal = Field(..., description="缺料数量")
    alert_level: str = Field(..., description="预警级别")
    expected_arrival_date: Optional[date] = Field(None, description="预计到货日期")
    days_to_required: int = Field(..., description="距需求天数")
    response_deadline: datetime = Field(..., description="响应截止时间")


class ShortageAlertListResponse(BaseModel):
    """缺料预警列表响应"""
    total: int = Field(..., description="总数")
    l1_count: int = Field(..., description="L1停工预警数")
    l2_count: int = Field(..., description="L2紧急预警数")
    l3_count: int = Field(..., description="L3提前预警数")
    l4_count: int = Field(..., description="L4常规预警数")
    items: List[ShortageAlertItem] = Field(..., description="预警列表")


# ========== 排产建议 ==========
class SchedulingSuggestionBase(BaseModel):
    """排产建议基础Schema"""
    suggestion_no: str = Field(..., max_length=50, description="建议单号")
    project_id: int = Field(..., description="项目ID")
    machine_id: Optional[int] = Field(None, description="机台ID")
    readiness_id: Optional[int] = Field(None, description="齐套分析ID")
    suggestion_type: str = Field(..., max_length=20, description="建议类型")
    priority_score: Decimal = Field(..., description="优先级得分")
    current_kit_rate: Decimal = Field(..., description="当前齐套率(%)")
    blocking_kit_rate: Decimal = Field(..., description="阻塞齐套率(%)")
    suggested_start_date: date = Field(..., description="建议开工日期")
    reason: Optional[str] = Field(None, description="建议原因")


class SchedulingSuggestionCreate(BaseModel):
    """创建排产建议请求(通常由系统自动生成)"""
    project_id: int = Field(..., description="项目ID")
    machine_id: Optional[int] = Field(None, description="机台ID")


class SchedulingSuggestionResponse(SchedulingSuggestionBase):
    """排产建议响应"""
    id: int
    status: str = Field(..., description="状态")
    project_no: Optional[str] = None
    project_name: Optional[str] = None
    machine_no: Optional[str] = None
    accepted_by: Optional[int] = None
    accepted_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SchedulingSuggestionAccept(BaseModel):
    """接受排产建议"""
    actual_start_date: Optional[date] = Field(None, description="实际开工日期，默认使用建议日期")


class SchedulingSuggestionReject(BaseModel):
    """拒绝排产建议"""
    reject_reason: str = Field(..., max_length=500, description="拒绝原因")


# ========== 看板数据 ==========
class AssemblyDashboardStats(BaseModel):
    """装配齐套看板统计"""
    total_projects: int = Field(..., description="项目总数")
    can_start_count: int = Field(..., description="可开工数量")
    partial_ready_count: int = Field(..., description="部分齐套数量")
    not_ready_count: int = Field(..., description="未齐套数量")
    avg_kit_rate: Decimal = Field(..., description="平均齐套率(%)")
    avg_blocking_rate: Decimal = Field(..., description="平均阻塞齐套率(%)")


class AssemblyDashboardStageStats(BaseModel):
    """分阶段统计"""
    stage_code: str
    stage_name: str
    can_start_count: int = Field(..., description="该阶段可开始的项目数")
    blocked_count: int = Field(..., description="该阶段被阻塞的项目数")
    avg_kit_rate: Decimal = Field(..., description="该阶段平均齐套率(%)")


class AssemblyDashboardResponse(BaseModel):
    """装配齐套看板响应"""
    stats: AssemblyDashboardStats = Field(..., description="总体统计")
    stage_stats: List[AssemblyDashboardStageStats] = Field(..., description="分阶段统计")
    alert_summary: Dict[str, int] = Field(..., description="预警汇总")
    recent_analyses: List[MaterialReadinessResponse] = Field(..., description="最近分析列表")
    pending_suggestions: List[SchedulingSuggestionResponse] = Field(..., description="待处理建议")


# ========== 通用响应 ==========
class AssemblyKitListResponse(BaseModel):
    """列表响应"""
    total: int
    items: List[Any]
    page: int = 1
    page_size: int = 20


# Forward references update
MaterialReadinessDetailResponse.model_rebuild()
