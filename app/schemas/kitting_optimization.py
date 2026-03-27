# -*- coding: utf-8 -*-
"""
齐套率优化模块 - Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 1. 缺料催货 ====================

class ExpediteTarget(BaseModel):
    """单条催货目标"""
    material_id: int = Field(description="物料ID")
    shortage_id: Optional[int] = Field(None, description="缺料预警ID")
    purchase_order_id: Optional[int] = Field(None, description="采购订单ID")
    urgency_level: str = Field(default="NORMAL", description="紧急程度: CRITICAL/HIGH/NORMAL/LOW")
    remark: Optional[str] = Field(None, description="催货备注")


class ExpediteRequest(BaseModel):
    """批量催货请求"""
    targets: List[ExpediteTarget] = Field(min_length=1, description="催货目标列表")
    notify_methods: List[str] = Field(
        default=["SYSTEM"],
        description="通知方式: EMAIL/SMS/WECHAT/SYSTEM",
    )
    auto_detect_high_risk: bool = Field(
        default=False,
        description="是否自动识别高风险缺料并加入催货",
    )
    project_id: Optional[int] = Field(None, description="项目ID(用于自动识别)")


class ExpediteRecordResponse(BaseModel):
    """催货记录响应"""
    id: int
    material_id: int
    material_code: str
    material_name: str
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_order_id: Optional[int] = None
    shortage_id: Optional[int] = None
    urgency_level: str
    shortage_qty: Optional[float] = None
    required_date: Optional[date] = None
    original_promised_date: Optional[date] = None
    new_promised_date: Optional[date] = None
    notify_method: str
    notify_status: str
    status: str
    supplier_response: Optional[str] = None
    actual_delivery_date: Optional[date] = None
    is_on_time: Optional[bool] = None
    created_at: Optional[datetime] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class ExpediteResult(BaseModel):
    """催货批量结果"""
    total_created: int = Field(description="创建催货记录数")
    auto_detected: int = Field(default=0, description="自动识别高风险数")
    notify_sent: int = Field(default=0, description="通知已发送数")
    notify_pending: int = Field(default=0, description="通知待发送数")
    records: List[ExpediteRecordResponse] = Field(description="催货记录列表")


class ExpediteStats(BaseModel):
    """催货效果统计"""
    total_expedited: int = Field(description="总催货次数")
    resolved_count: int = Field(description="已解决数")
    on_time_count: int = Field(description="催后准时到货数")
    on_time_rate: float = Field(description="催后准时率(%)")
    avg_response_days: Optional[float] = Field(None, description="平均响应天数")
    by_urgency: Dict[str, int] = Field(default={}, description="按紧急程度统计")
    by_supplier: List[Dict[str, Any]] = Field(default=[], description="按供应商统计")


# ==================== 2. 替代料推荐 ====================

class AlternativeMaterialResponse(BaseModel):
    """替代料信息"""
    id: int
    alternative_material_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    match_score: float = Field(description="匹配度(0-100)")
    match_reason: Optional[str] = None
    is_verified: bool = False

    # 库存信息
    current_stock: float = Field(default=0, description="当前库存")
    available_stock: float = Field(default=0, description="可用库存")

    # 价格对比
    original_price: Optional[float] = None
    alternative_price: Optional[float] = None
    price_diff_pct: Optional[float] = Field(None, description="价格差异(%)")

    # 供应商
    supplier_count: int = Field(default=0, description="可供应商家数")
    lead_time_days: Optional[int] = Field(None, description="采购周期(天)")

    # ECN
    ecn_no: Optional[str] = None
    ecn_status: Optional[str] = None

    class Config:
        from_attributes = True


class AlternativeListResponse(BaseModel):
    """替代料列表响应"""
    original_material_id: int
    original_material_code: str
    original_material_name: str
    original_specification: Optional[str] = None
    alternatives: List[AlternativeMaterialResponse]
    total: int


# ==================== 3. 安全库存预警 ====================

class SafetyStockAlert(BaseModel):
    """安全库存预警条目"""
    material_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    category_name: Optional[str] = None
    is_key_material: bool = False

    # 库存数据
    current_stock: float
    safety_stock: float
    gap: float = Field(description="缺口数量(安全库存-当前库存)")
    gap_pct: float = Field(description="缺口百分比")

    # 消耗分析
    avg_daily_consumption: float = Field(description="日均消耗量")
    days_of_supply: Optional[float] = Field(None, description="可供天数")

    # 补货建议
    lead_time_days: int = Field(default=0, description="采购周期(天)")
    suggested_reorder_qty: float = Field(description="建议补货数量")
    reorder_point: float = Field(description="补货点")
    estimated_stockout_date: Optional[date] = Field(None, description="预计断料日期")

    # 监控级别
    alert_level: str = Field(description="预警级别: CRITICAL/WARNING/INFO")
    is_high_frequency_shortage: bool = Field(default=False, description="是否高频缺料物料")
    shortage_count_90d: int = Field(default=0, description="近90天缺料次数")


class SafetyStockAlertResponse(BaseModel):
    """安全库存预警响应"""
    alerts: List[SafetyStockAlert]
    total: int
    critical_count: int = Field(description="紧急预警数")
    warning_count: int = Field(description="警告数")
    summary: Dict[str, Any] = Field(default={}, description="汇总统计")


# ==================== 4. 齐套率改进建议 ====================

class BottleneckMaterial(BaseModel):
    """瓶颈物料"""
    material_id: int
    material_code: str
    material_name: str
    shortage_count: int = Field(description="缺料次数")
    total_shortage_qty: float = Field(description="累计缺料数量")
    avg_delay_days: Optional[float] = Field(None, description="平均延迟天数")
    affected_projects: int = Field(description="影响项目数")
    suggestion: str = Field(description="改进建议")


class SupplierDeliveryAnalysis(BaseModel):
    """供应商交期分析"""
    supplier_id: int
    supplier_name: str
    total_orders: int = Field(description="总订单数")
    on_time_count: int = Field(description="准时交货数")
    delayed_count: int = Field(description="延迟交货数")
    on_time_rate: float = Field(description="准时交货率(%)")
    avg_delay_days: float = Field(description="平均延迟天数")
    max_delay_days: int = Field(description="最大延迟天数")
    risk_level: str = Field(description="风险等级: HIGH/MEDIUM/LOW")
    suggestion: str = Field(description="改进建议")


class PrePurchaseMaterial(BaseModel):
    """建议提前采购物料"""
    material_id: int
    material_code: str
    material_name: str
    lead_time_days: int
    avg_monthly_usage: float
    current_stock: float
    reason: str = Field(description="提前采购原因")
    suggested_qty: float = Field(description="建议采购数量")
    suggested_order_date: Optional[date] = Field(None, description="建议下单日期")


class CommonStockMaterial(BaseModel):
    """建议备库的通用物料"""
    material_id: int
    material_code: str
    material_name: str
    usage_frequency: int = Field(description="使用频次(近6个月)")
    project_coverage: int = Field(description="覆盖项目数")
    current_stock: float
    suggested_safety_stock: float
    reason: str


class ImprovementTarget(BaseModel):
    """齐套率改进目标"""
    current_rate: float = Field(description="当前齐套率(%)")
    target_rate: float = Field(description="目标齐套率(%)")
    gap: float = Field(description="差距(%)")
    key_actions: List[str] = Field(description="关键行动项")
    estimated_timeline: str = Field(description="预计达成时间")


class KittingImprovementSuggestions(BaseModel):
    """齐套率改进建议汇总"""
    bottleneck_materials: List[BottleneckMaterial] = Field(description="瓶颈物料TOP10")
    supplier_analysis: List[SupplierDeliveryAnalysis] = Field(description="供应商交期分析")
    pre_purchase_materials: List[PrePurchaseMaterial] = Field(description="建议提前采购物料")
    common_stock_materials: List[CommonStockMaterial] = Field(description="建议备库通用物料")
    improvement_target: ImprovementTarget = Field(description="改进目标及路径")
    generated_at: datetime = Field(description="生成时间")
