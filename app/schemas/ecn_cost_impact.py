# -*- coding: utf-8 -*-
"""
ECN成本影响跟踪 Schema

覆盖：
1. ECN成本影响分析
2. ECN成本执行跟踪
3. ECN成本记录CRUD
4. 项目ECN成本汇总
5. ECN成本预警
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema


# ==================== 成本记录 ====================


class EcnCostRecordCreate(BaseModel):
    """创建ECN成本记录"""

    ecn_id: int = Field(description="ECN ID")
    project_id: Optional[int] = None
    machine_id: Optional[int] = None

    cost_type: str = Field(
        description="成本类型: SCRAP/REWORK/NEW_PURCHASE/CLAIM/DELAY/ADMIN"
    )
    cost_category: Optional[str] = None

    estimated_amount: Decimal = Field(default=0, description="预估金额")
    actual_amount: Decimal = Field(default=0, description="实际金额")
    currency: str = Field(default="CNY")
    cost_date: Optional[date] = None

    # 物料关联
    material_id: Optional[int] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

    # 返工
    rework_hours: Optional[float] = None
    hourly_rate: Optional[float] = None

    # 凭证
    voucher_type: Optional[str] = None
    voucher_no: Optional[str] = None
    voucher_attachment_id: Optional[int] = None

    # 供应商
    vendor_id: Optional[int] = None

    description: Optional[str] = None


class EcnCostRecordResponse(TimestampSchema):
    """成本记录响应"""

    id: int
    ecn_id: int
    project_id: Optional[int] = None
    machine_id: Optional[int] = None

    cost_type: str
    cost_category: Optional[str] = None

    estimated_amount: Decimal = 0
    actual_amount: Decimal = 0
    currency: str = "CNY"
    cost_date: Optional[date] = None

    material_id: Optional[int] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

    rework_hours: Optional[float] = None
    hourly_rate: Optional[float] = None

    voucher_type: Optional[str] = None
    voucher_no: Optional[str] = None

    vendor_id: Optional[int] = None
    description: Optional[str] = None

    approval_status: str = "PENDING"
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None

    recorded_by: int


# ==================== 成本影响分析 ====================


class CostImpactByType(BaseModel):
    """按类型分类的成本"""

    cost_type: str
    cost_type_label: str
    estimated_total: Decimal = 0
    actual_total: Decimal = 0
    record_count: int = 0


class MaterialCostImpact(BaseModel):
    """物料级别成本影响"""

    material_id: Optional[int] = None
    material_code: str
    material_name: str
    scrap_cost: Decimal = 0
    new_purchase_cost: Decimal = 0
    total_impact: Decimal = 0


class CostImpactAnalysisResponse(BaseModel):
    """成本影响分析响应"""

    ecn_id: int
    ecn_no: str
    project_id: Optional[int] = None

    # 直接成本
    scrap_cost: Decimal = Field(default=0, description="物料报废成本")
    rework_cost: Decimal = Field(default=0, description="返工成本")
    new_purchase_cost: Decimal = Field(default=0, description="新物料采购成本")

    # 间接成本
    claim_cost: Decimal = Field(default=0, description="供应商索赔成本")
    delay_cost: Decimal = Field(default=0, description="延期成本")
    admin_cost: Decimal = Field(default=0, description="管理成本")

    # 汇总
    direct_cost_total: Decimal = Field(default=0, description="直接成本合计")
    indirect_cost_total: Decimal = Field(default=0, description="间接成本合计")
    total_cost_impact: Decimal = Field(default=0, description="总成本影响")

    # 分类明细
    cost_by_type: List[CostImpactByType] = []

    # 物料成本影响排行
    top_material_impacts: List[MaterialCostImpact] = []

    # 从已有评估数据
    assessed_cost_impact: Decimal = Field(default=0, description="评估阶段预估总成本")

    analyzed_at: datetime


# ==================== 成本执行跟踪 ====================


class CostTrendItem(BaseModel):
    """成本趋势项"""

    period: str  # YYYY-MM
    estimated: Decimal = 0
    actual: Decimal = 0
    cumulative_actual: Decimal = 0


class CostTrackingResponse(BaseModel):
    """成本执行跟踪响应"""

    ecn_id: int
    ecn_no: str

    # 预算 vs 实际
    total_estimated: Decimal = 0
    total_actual: Decimal = 0
    variance: Decimal = Field(default=0, description="偏差 (实际 - 预估)")
    variance_ratio: float = Field(default=0, description="偏差率(%)")

    # 按类型
    cost_by_type: List[CostImpactByType] = []

    # 趋势
    cost_trend: List[CostTrendItem] = []

    # 预计最终成本
    forecast_final_cost: Decimal = Field(default=0, description="预计最终成本")

    # 记录统计
    total_records: int = 0
    approved_records: int = 0
    pending_records: int = 0


# ==================== 项目ECN成本汇总 ====================


class EcnCostSummaryItem(BaseModel):
    """单个ECN的成本汇总"""

    ecn_id: int
    ecn_no: str
    ecn_title: str
    status: str
    total_estimated: Decimal = 0
    total_actual: Decimal = 0
    record_count: int = 0


class ProjectEcnCostSummaryResponse(BaseModel):
    """项目ECN成本汇总响应"""

    project_id: int
    project_name: Optional[str] = None

    # 汇总
    total_ecn_count: int = 0
    total_estimated_cost: Decimal = 0
    total_actual_cost: Decimal = 0

    # 占比
    project_budget: Optional[Decimal] = None
    ecn_cost_ratio: Optional[float] = Field(
        default=None, description="ECN成本占项目预算比例(%)"
    )

    # 按ECN分类
    ecn_details: List[EcnCostSummaryItem] = []

    # 按成本类型
    cost_by_type: List[CostImpactByType] = []


# ==================== 成本预警 ====================


class CostAlertCreate(BaseModel):
    """成本预警配置"""

    ecn_id: int
    budget_threshold: Optional[Decimal] = Field(
        default=None, description="预算阈值，超过则预警"
    )
    large_amount_threshold: Optional[Decimal] = Field(
        default=None, description="大额成本阈值，单笔超过则提醒审批"
    )
    trend_check: bool = Field(default=True, description="是否检查成本趋势异常")


class CostAlertItem(BaseModel):
    """单条预警"""

    alert_type: str  # OVER_BUDGET / LARGE_AMOUNT / TREND_ABNORMAL
    alert_level: str  # WARNING / CRITICAL
    message: str
    current_value: Decimal = 0
    threshold_value: Optional[Decimal] = None
    related_record_id: Optional[int] = None


class CostAlertResponse(BaseModel):
    """成本预警响应"""

    ecn_id: int
    ecn_no: str
    alerts: List[CostAlertItem] = []
    total_estimated: Decimal = 0
    total_actual: Decimal = 0
    alert_count: int = 0
    checked_at: datetime
