# -*- coding: utf-8 -*-
"""
项目-变更单联动集成 Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema


# ==================== 影响评估请求 ====================


class MilestoneImpactItem(BaseModel):
    """单个里程碑影响"""

    milestone_id: int
    name: str
    original_date: Optional[str] = None
    new_date: Optional[str] = None
    delay_days: int = 0


class CostBreakdown(BaseModel):
    """成本明细"""

    rework_hours: float = 0
    hourly_rate: float = 0
    scrap_materials: Optional[List[Dict[str, Any]]] = None
    new_materials: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None


class AssessImpactRequest(BaseModel):
    """ECN 审批时 — 影响评估请求"""

    ecn_id: int = Field(description="ECN ID")
    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None

    # 进度影响
    schedule_impact_days: int = Field(default=0, description="预计延期天数")
    affected_milestones: Optional[List[MilestoneImpactItem]] = None

    # 成本影响
    rework_cost: Decimal = Field(default=0, description="返工成本")
    scrap_cost: Decimal = Field(default=0, description="报废成本")
    additional_cost: Decimal = Field(default=0, description="新增成本")
    cost_breakdown: Optional[CostBreakdown] = None

    # 风险
    risk_level: str = Field(default="LOW", description="风险等级: LOW/MEDIUM/HIGH/CRITICAL")
    risk_description: Optional[str] = None

    # 报告
    impact_summary: Optional[str] = None
    remark: Optional[str] = None


# ==================== 执行联动请求 ====================


class ExecuteLinkageRequest(BaseModel):
    """ECN 执行后 — 联动更新请求"""

    impact_id: int = Field(description="影响记录ID")

    # 是否自动执行各联动操作
    update_milestones: bool = Field(default=True, description="是否更新里程碑计划")
    record_costs: bool = Field(default=True, description="是否记录项目成本")
    create_risk: bool = Field(default=True, description="是否创建风险记录")

    # 实际影响（可覆盖评估值）
    actual_delay_days: Optional[int] = None
    actual_cost_impact: Optional[Decimal] = None

    remark: Optional[str] = None


# ==================== 响应 ====================


class ProjectChangeImpactResponse(TimestampSchema):
    """影响记录响应"""

    id: int
    ecn_id: int
    ecn_no: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None

    # 评估
    project_stage_snapshot: Optional[str] = None
    project_progress_snapshot: Optional[float] = None
    schedule_impact_days: int = 0
    affected_milestones: Optional[List[Dict[str, Any]]] = None
    rework_cost: Decimal = 0
    scrap_cost: Decimal = 0
    additional_cost: Decimal = 0
    total_cost_impact: Decimal = 0
    cost_breakdown: Optional[Dict[str, Any]] = None
    risk_level: str = "LOW"
    risk_description: Optional[str] = None
    impact_summary: Optional[str] = None
    assessed_by: Optional[int] = None
    assessed_at: Optional[datetime] = None

    # 执行
    milestones_updated: bool = False
    costs_recorded: bool = False
    risk_created: bool = False
    actual_delay_days: Optional[int] = None
    actual_cost_impact: Optional[Decimal] = None
    status: str = "ASSESSED"
    executed_by: Optional[int] = None
    executed_at: Optional[datetime] = None
    remark: Optional[str] = None


class ProjectChangeImpactListResponse(BaseModel):
    """影响记录列表项"""

    id: int
    ecn_id: int
    ecn_no: str
    ecn_title: Optional[str] = None
    project_id: int
    project_name: Optional[str] = None
    schedule_impact_days: int = 0
    total_cost_impact: Decimal = 0
    risk_level: str = "LOW"
    status: str = "ASSESSED"
    assessed_at: Optional[datetime] = None
    created_at: datetime


class ProjectChangeSummary(BaseModel):
    """项目变更影响汇总"""

    project_id: int
    project_name: Optional[str] = None
    total_ecn_count: int = 0
    assessed_count: int = 0
    executing_count: int = 0
    completed_count: int = 0
    total_delay_days: int = 0
    total_cost_impact: Decimal = 0
    high_risk_count: int = 0
    impacts: List[ProjectChangeImpactListResponse] = []


class ImpactAssessmentReport(BaseModel):
    """影响评估报告（ECN 审批时返回）"""

    ecn_id: int
    ecn_no: str
    project_id: int
    project_name: Optional[str] = None
    project_stage: Optional[str] = None
    project_progress: Optional[float] = None

    # 进度影响
    schedule_impact_days: int = 0
    affected_milestone_count: int = 0
    affected_milestones: Optional[List[Dict[str, Any]]] = None

    # 成本影响
    rework_cost: Decimal = 0
    scrap_cost: Decimal = 0
    additional_cost: Decimal = 0
    total_cost_impact: Decimal = 0

    # 风险
    risk_level: str = "LOW"
    risk_description: Optional[str] = None

    # 综合评估
    impact_summary: str = ""
    recommendation: Optional[str] = None

    # 记录ID
    impact_record_id: Optional[int] = None
