# -*- coding: utf-8 -*-
"""
项目分析和管理 Schema
包含项目分析、批量操作、状态管理等高级功能的 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema

# ==================== 项目状态变更历史 ====================


class ProjectHealthDetailsResponse(BaseModel):
    """项目健康度详情响应"""
    project_id: int
    project_code: str
    current_health: str
    calculated_health: str
    status: str
    stage: str
    checks: dict
    statistics: dict

    class Config:
        from_attributes = True


class ProjectStatusLogResponse(BaseSchema):
    """项目状态变更历史响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None

    # 变更前状态
    old_stage: Optional[str] = None
    old_status: Optional[str] = None
    old_health: Optional[str] = None

    # 变更后状态
    new_stage: Optional[str] = None
    new_status: Optional[str] = None
    new_health: Optional[str] = None

    # 变更信息
    change_type: str
    change_reason: Optional[str] = None
    change_note: Optional[str] = None

    # 操作信息
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


# ==================== 项目复制和归档 ====================


class ProjectCloneRequest(BaseModel):
    """项目复制请求"""

    new_project_code: str = Field(max_length=50, description="新项目编码")
    new_project_name: str = Field(max_length=200, description="新项目名称")
    copy_machines: Optional[bool] = Field(default=True, description="是否复制机台")
    copy_milestones: Optional[bool] = Field(default=True, description="是否复制里程碑")
    copy_members: Optional[bool] = Field(default=True, description="是否复制成员")
    copy_stages: Optional[bool] = Field(default=True, description="是否复制阶段")
    customer_id: Optional[int] = Field(default=None, description="新客户ID（可选，默认使用原客户）")


class ProjectArchiveRequest(BaseModel):
    """项目归档请求"""

    archive_reason: Optional[str] = Field(default=None, max_length=500, description="归档原因")


# ==================== 资源分配优化 ====================


class ResourceConflictResponse(BaseModel):
    """资源冲突响应"""

    resource_id: int
    resource_name: str
    conflict_type: str  # OVERLOAD, OVERLAP
    conflict_projects: List[dict]
    conflict_period: dict
    suggested_solution: Optional[str] = None


class ResourceOptimizationResponse(BaseModel):
    """资源分配优化响应"""

    conflicts: List[ResourceConflictResponse]
    overloaded_resources: List[dict]
    underutilized_resources: List[dict]
    optimization_suggestions: List[str]


# ==================== 项目关联分析 ====================


class ProjectRelationResponse(BaseModel):
    """项目关联响应"""

    project_id: int
    project_code: str
    project_name: str
    relation_type: str  # SHARED_RESOURCE, DEPENDENCY, SIMILAR, CUSTOMER
    relation_strength: str  # WEAK, MEDIUM, STRONG
    related_projects: List[dict]
    shared_resources: List[dict]
    dependency_info: Optional[dict] = None


# ==================== 风险矩阵 ====================


class RiskMatrixResponse(BaseModel):
    """风险矩阵响应"""

    matrix_data: List[dict]  # [{probability, impact, count, risks: [...]}]
    risk_distribution: dict
    high_priority_risks: List[dict]
    risk_trends: Optional[List[dict]] = None


# ==================== 变更影响分析 ====================


class ChangeImpactRequest(BaseModel):
    """变更影响分析请求"""

    change_type: str  # SCOPE, SCHEDULE, COST, RESOURCE
    change_description: str
    affected_items: Optional[List[dict]] = None


class ChangeImpactResponse(BaseModel):
    """变更影响分析响应"""

    affected_projects: List[dict]
    affected_tasks: List[dict]
    affected_resources: List[dict]
    cost_impact: Optional[dict] = None
    schedule_impact: Optional[dict] = None
    risk_impact: Optional[dict] = None
    recommendations: List[str]


# ==================== 项目概览和时间线 ====================


class ProjectSummaryResponse(BaseModel):
    """项目概览数据响应"""

    project_id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    pm_name: Optional[str] = None
    stage: str
    status: str
    health: Optional[str] = None
    progress_pct: float
    contract_amount: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    machine_count: int = 0
    milestone_count: int = 0
    completed_milestone_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    member_count: int = 0
    alert_count: int = 0
    issue_count: int = 0
    document_count: int = 0
    cost_summary: Optional[dict] = None
    recent_activities: Optional[List[dict]] = None


class TimelineEvent(BaseModel):
    """时间线事件"""

    event_type: str  # STAGE_CHANGE, STATUS_CHANGE, MILESTONE, TASK, COST, DOCUMENT, etc.
    event_time: datetime
    title: str
    description: Optional[str] = None
    user_name: Optional[str] = None
    related_id: Optional[int] = None
    related_type: Optional[str] = None


class ProjectTimelineResponse(BaseModel):
    """项目时间线响应"""

    project_id: int
    project_code: str
    project_name: str
    events: List[TimelineEvent]
    total_events: int


# ==================== 阶段推进和门控 ====================


class StageAdvanceRequest(BaseModel):
    """阶段推进请求"""

    target_stage: str = Field(..., description="目标阶段（S1-S9）")
    reason: Optional[str] = Field(None, description="推进原因")
    skip_gate_check: bool = Field(False, description="是否跳过阶段门校验（仅管理员）")


class GateCheckCondition(BaseModel):
    """阶段门校验条件项"""

    condition_name: str = Field(..., description="条件名称")
    condition_desc: str = Field(..., description="条件描述")
    status: str = Field(..., description="检查状态：PASSED/FAILED/PENDING")
    message: Optional[str] = Field(None, description="检查结果消息")
    action_url: Optional[str] = Field(None, description="处理链接（如需要）")
    action_text: Optional[str] = Field(None, description="处理按钮文本")


class GateCheckResult(BaseModel):
    """阶段门校验结果（Issue 1.4: 详细反馈）"""

    gate_code: str = Field(..., description="阶段门编码（G1-G8）")
    gate_name: str = Field(..., description="阶段门名称")
    from_stage: str = Field(..., description="源阶段")
    to_stage: str = Field(..., description="目标阶段")
    passed: bool = Field(..., description="是否通过")
    total_conditions: int = Field(..., description="总条件数")
    passed_conditions: int = Field(..., description="通过条件数")
    failed_conditions: int = Field(..., description="失败条件数")
    conditions: List[GateCheckCondition] = Field(default_factory=list, description="条件检查详情")
    missing_items: List[str] = Field(default_factory=list, description="缺失项列表（兼容旧格式）")
    suggestions: List[str] = Field(default_factory=list, description="建议操作")
    progress_pct: float = Field(..., description="完成进度百分比")


class StageAdvanceResponse(BaseModel):
    """阶段推进响应"""

    project_id: int
    project_code: str
    project_name: str
    old_stage: str
    new_stage: str
    new_status: Optional[str] = None
    gate_passed: bool
    gate_check_result: Optional[GateCheckResult] = None
    missing_items: List[str] = []


# ==================== 项目三维状态 ====================


class ProjectStatusResponse(BaseModel):
    """项目三维状态响应"""

    project_id: int
    project_code: str
    project_name: str
    stage: str
    stage_name: Optional[str] = None
    status: str
    status_name: Optional[str] = None
    health: Optional[str] = None
    health_name: Optional[str] = None
    progress_pct: float
    last_updated: Optional[datetime] = None


# ==================== 批量操作 ====================


class BatchUpdateStatusRequest(BaseModel):
    """批量更新项目状态请求"""

    project_ids: List[int] = Field(..., description="项目ID列表")
    new_status: str = Field(..., description="新状态（ST01-ST30）")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchArchiveRequest(BaseModel):
    """批量归档项目请求"""

    project_ids: List[int] = Field(..., description="项目ID列表")
    archive_reason: Optional[str] = Field(None, description="归档原因")


class BatchAssignPMRequest(BaseModel):
    """批量分配项目经理请求"""

    project_ids: List[int] = Field(..., description="项目ID列表")
    pm_id: int = Field(..., description="项目经理ID")


class BatchUpdateStageRequest(BaseModel):
    """批量更新项目阶段请求"""

    project_ids: List[int] = Field(..., description="项目ID列表")
    new_stage: str = Field(..., description="新阶段（S1-S9）")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    success_count: int
    failed_count: int
    failed_projects: List[dict] = []


# ==================== 项目仪表盘 ====================


class ProjectDashboardResponse(BaseModel):
    """项目仪表盘响应"""

    project_id: int
    project_code: str
    project_name: str

    # 基本信息
    basic_info: dict

    # 进度统计
    progress_stats: dict

    # 成本统计
    cost_stats: dict

    # 任务统计
    task_stats: dict

    # 里程碑统计
    milestone_stats: dict

    # 风险统计
    risk_stats: Optional[dict] = None

    # 问题统计
    issue_stats: Optional[dict] = None

    # 资源使用
    resource_usage: Optional[dict] = None

    # 最近活动
    recent_activities: List[dict] = []

    # 关键指标
    key_metrics: dict


# ==================== 在产项目进度汇总 ====================


class InProductionProjectSummary(BaseModel):
    """在产项目进度汇总（给生产总监/经理看）"""
    project_id: int
    project_code: str
    project_name: str
    stage: str
    health: Optional[str] = None
    progress: float = 0.0
    planned_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    overdue_milestones_count: int = 0
    next_milestone: Optional[str] = None
    next_milestone_date: Optional[date] = None
