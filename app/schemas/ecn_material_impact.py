# -*- coding: utf-8 -*-
"""
ECN物料影响跟踪 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema


# ==================== 物料影响分析 ====================


class MaterialImpactItem(BaseModel):
    """单个受影响物料详情"""

    material_id: Optional[int] = None
    material_code: str
    material_name: str
    specification: Optional[str] = None
    material_status: str = Field(description="NOT_PURCHASED/ORDERED/IN_TRANSIT/IN_STOCK")
    affected_quantity: Decimal = 0
    unit_price: Decimal = 0
    potential_loss: Decimal = 0
    purchase_order_id: Optional[int] = None
    purchase_order_no: Optional[str] = None
    supplier_name: Optional[str] = None
    change_type: Optional[str] = None


class AffectedOrderSummary(BaseModel):
    """受影响采购订单摘要"""

    order_id: int
    order_no: str
    supplier_name: Optional[str] = None
    total_amount: Decimal = 0
    status: Optional[str] = None
    affected_item_count: int = 0


class ProjectImpactSummary(BaseModel):
    """对项目交付影响摘要"""

    project_id: int
    project_name: Optional[str] = None
    schedule_impact_days: int = 0
    affected_material_count: int = 0
    risk_level: Optional[str] = None


class MaterialImpactAnalysisResponse(BaseModel):
    """物料影响分析响应"""

    ecn_id: int
    ecn_no: str
    analysis_time: datetime

    # 受影响物料
    affected_materials: List[MaterialImpactItem] = []
    total_affected_count: int = 0

    # 按状态分组统计
    status_summary: Dict[str, int] = {}

    # 潜在损失
    total_potential_loss: Decimal = 0
    loss_by_status: Dict[str, Decimal] = {}

    # 受影响采购订单
    affected_orders: List[AffectedOrderSummary] = []

    # 项目影响
    project_impacts: List[ProjectImpactSummary] = []


# ==================== 执行进度 ====================


class ExecutionPhaseResponse(BaseModel):
    """执行阶段详情"""

    id: int
    phase: str
    phase_name: Optional[str] = None
    phase_order: int = 0
    status: str = "PENDING"
    progress_pct: int = 0
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_completion: Optional[date] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    is_blocked: bool = False
    block_reason: Optional[str] = None
    summary: Optional[str] = None


class MaterialDispositionStatus(BaseModel):
    """物料处置状态"""

    material_code: str
    material_name: str
    disposition: Optional[str] = None
    status: str = "PENDING"
    potential_loss: Decimal = 0
    actual_loss: Decimal = 0


class ExecutionProgressResponse(BaseModel):
    """ECN执行进度响应"""

    ecn_id: int
    ecn_no: str
    ecn_status: str
    overall_progress_pct: int = 0

    # 各阶段进度
    phases: List[ExecutionPhaseResponse] = []

    # 物料处置状态
    material_dispositions: List[MaterialDispositionStatus] = []

    # 阻塞问题
    blocked_phases: List[ExecutionPhaseResponse] = []

    # 时间
    execution_start: Optional[datetime] = None
    estimated_completion: Optional[date] = None


# ==================== 相关人员 ====================


class StakeholderResponse(BaseModel):
    """相关人员响应"""

    id: int
    ecn_id: int
    user_id: int
    user_name: Optional[str] = None
    department: Optional[str] = None
    role: str
    role_name: Optional[str] = None
    source: str = "AUTO"
    source_reason: Optional[str] = None
    is_subscribed: bool = True
    subscription_types: Optional[List[str]] = None
    can_view_detail: bool = True
    can_view_progress: bool = True


class StakeholderListResponse(BaseModel):
    """相关人员列表响应"""

    ecn_id: int
    ecn_no: str
    stakeholders: List[StakeholderResponse] = []
    total_count: int = 0
    by_role: Dict[str, int] = {}


# ==================== 通知 ====================


class NotifyStakeholdersRequest(BaseModel):
    """通知相关人员请求"""

    notification_type: str = Field(
        description="通知类型: ECN_PUBLISHED/STATUS_CHANGE/DISPOSITION_UPDATE/PROGRESS_MILESTONE"
    )
    message: Optional[str] = Field(default=None, description="自定义消息内容")
    target_roles: Optional[List[str]] = Field(
        default=None, description="目标角色列表，为空则通知所有订阅人"
    )
    priority: str = Field(default="NORMAL", description="优先级: LOW/NORMAL/HIGH/URGENT")


class NotifyResultResponse(BaseModel):
    """通知结果响应"""

    ecn_id: int
    notification_type: str
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    details: List[Dict[str, Any]] = []


# ==================== 物料处置 ====================


class MaterialDispositionRequest(BaseModel):
    """物料处置请求"""

    disposition: str = Field(
        description="处置方式: CONTINUE_USE/REWORK/SCRAP/RETURN"
    )
    disposition_reason: str = Field(description="处置原因")
    disposition_cost: Decimal = Field(default=0, description="处置成本")
    remark: Optional[str] = None


class MaterialDispositionResponse(TimestampSchema):
    """物料处置响应"""

    id: int
    ecn_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    material_status: str
    affected_quantity: Decimal = 0
    potential_loss: Decimal = 0
    disposition: Optional[str] = None
    disposition_reason: Optional[str] = None
    disposition_cost: Decimal = 0
    actual_loss: Decimal = 0
    status: str = "PENDING"
    decided_by: Optional[int] = None
    decided_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    purchase_order_no: Optional[str] = None
    supplier_name: Optional[str] = None


# ==================== 订阅管理 ====================


class SubscriptionUpdateRequest(BaseModel):
    """订阅更新请求"""

    is_subscribed: bool
    subscription_types: Optional[List[str]] = None
