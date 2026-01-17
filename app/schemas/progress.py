# -*- coding: utf-8 -*-
"""
进度跟踪模块 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema, PaginatedResponse, TimestampSchema

# ==================== WBS 模板 ====================

class WbsTemplateCreate(BaseModel):
    """创建WBS模板"""
    template_code: str = Field(max_length=20, description="模板编码")
    template_name: str = Field(max_length=100, description="模板名称")
    project_type: Optional[str] = Field(default=None, max_length=20, description="项目类型")
    equipment_type: Optional[str] = Field(default=None, max_length=20, description="设备类型")
    version_no: Optional[str] = Field(default="V1", max_length=10, description="版本号")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class WbsTemplateUpdate(BaseModel):
    """更新WBS模板"""
    template_name: Optional[str] = None
    project_type: Optional[str] = None
    equipment_type: Optional[str] = None
    version_no: Optional[str] = None
    is_active: Optional[bool] = None


class WbsTemplateResponse(TimestampSchema):
    """WBS模板响应"""
    id: int
    template_code: str
    template_name: str
    project_type: Optional[str] = None
    equipment_type: Optional[str] = None
    version_no: str
    is_active: bool


class WbsTemplateListResponse(PaginatedResponse):
    """WBS模板列表响应"""
    items: List[WbsTemplateResponse]


# ==================== WBS 模板任务 ====================

class WbsTemplateTaskCreate(BaseModel):
    """创建WBS模板任务"""
    task_name: str = Field(max_length=200, description="任务名称")
    stage: Optional[str] = Field(default=None, max_length=20, description="阶段（S1-S9）")
    default_owner_role: Optional[str] = Field(default=None, max_length=50, description="默认负责人角色")
    plan_days: Optional[int] = Field(default=None, description="计划天数")
    weight: Optional[Decimal] = Field(default=Decimal("1.00"), description="权重")
    depends_on_template_task_id: Optional[int] = Field(default=None, description="依赖的模板任务ID")


class WbsTemplateTaskUpdate(BaseModel):
    """更新WBS模板任务"""
    task_name: Optional[str] = None
    stage: Optional[str] = None
    default_owner_role: Optional[str] = None
    plan_days: Optional[int] = None
    weight: Optional[Decimal] = None
    depends_on_template_task_id: Optional[int] = None


class WbsTemplateTaskResponse(BaseSchema):
    """WBS模板任务响应"""
    id: int
    template_id: int
    task_name: str
    stage: Optional[str] = None
    default_owner_role: Optional[str] = None
    plan_days: Optional[int] = None
    weight: Decimal
    depends_on_template_task_id: Optional[int] = None


# ==================== 项目任务 ====================

class TaskCreate(BaseModel):
    """创建项目任务"""
    task_name: str = Field(max_length=200, description="任务名称")
    machine_id: Optional[int] = Field(default=None, description="机台ID")
    milestone_id: Optional[int] = Field(default=None, description="里程碑ID")
    stage: Optional[str] = Field(default=None, max_length=20, description="阶段（S1-S9）")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    plan_start: Optional[date] = Field(default=None, description="计划开始日期")
    plan_end: Optional[date] = Field(default=None, description="计划结束日期")
    weight: Optional[Decimal] = Field(default=Decimal("1.00"), description="权重")


class TaskUpdate(BaseModel):
    """更新项目任务"""
    task_name: Optional[str] = None
    machine_id: Optional[int] = None
    milestone_id: Optional[int] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100, description="进度百分比")
    weight: Optional[Decimal] = None
    block_reason: Optional[str] = None


class TaskProgressUpdate(BaseModel):
    """更新任务进度"""
    progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    update_note: Optional[str] = Field(default=None, description="更新说明")


class TaskResponse(TimestampSchema):
    """任务响应"""
    id: int
    project_id: int
    machine_id: Optional[int] = None
    milestone_id: Optional[int] = None
    task_name: str
    stage: Optional[str] = None
    status: str
    owner_id: Optional[int] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress_percent: int
    weight: Decimal
    block_reason: Optional[str] = None


class TaskListResponse(PaginatedResponse):
    """任务列表响应"""
    items: List[TaskResponse]


# ==================== 从模板初始化WBS ====================

class InitWbsRequest(BaseModel):
    """从模板初始化WBS请求"""
    template_id: int = Field(description="WBS模板ID")
    start_date: Optional[date] = Field(default=None, description="计划开始日期（可选，默认使用项目开始日期）")
    assign_owners: Optional[bool] = Field(default=False, description="是否自动分配负责人（根据角色）")


class InitWbsResponse(BaseModel):
    """从模板初始化WBS响应"""
    code: int = 200
    message: str
    data: Optional[dict] = None


# ==================== 进度填报 ====================

class ProgressReportCreate(BaseModel):
    """创建进度报告"""
    report_type: str = Field(description="报告类型：daily/weekly")
    report_date: date = Field(description="报告日期")
    project_id: Optional[int] = Field(default=None, description="项目ID（项目报告）")
    machine_id: Optional[int] = Field(default=None, description="机台ID（机台报告）")
    task_id: Optional[int] = Field(default=None, description="任务ID（任务报告）")
    content: str = Field(description="报告内容")
    completed_work: Optional[str] = Field(default=None, description="已完成工作")
    planned_work: Optional[str] = Field(default=None, description="计划工作")
    issues: Optional[str] = Field(default=None, description="问题与阻塞")
    next_plan: Optional[str] = Field(default=None, description="下一步计划")


class ProgressReportUpdate(BaseModel):
    """更新进度报告"""
    report_type: Optional[str] = Field(default=None, description="报告类型：daily/weekly")
    report_date: Optional[date] = Field(default=None, description="报告日期")
    content: Optional[str] = Field(default=None, description="报告内容")
    completed_work: Optional[str] = Field(default=None, description="已完成工作")
    planned_work: Optional[str] = Field(default=None, description="计划工作")
    issues: Optional[str] = Field(default=None, description="问题与阻塞")
    next_plan: Optional[str] = Field(default=None, description="下一步计划")


class ProgressReportResponse(TimestampSchema):
    """进度报告响应"""
    id: int
    report_type: str
    report_date: date
    project_id: Optional[int] = None
    machine_id: Optional[int] = None
    task_id: Optional[int] = None
    content: str
    completed_work: Optional[str] = None
    planned_work: Optional[str] = None
    issues: Optional[str] = None


# ==================== 智能进度预测与依赖检查 ====================


class TaskForecastItem(BaseModel):
    """任务预测项"""

    task_id: int
    task_name: str
    progress_percent: int
    predicted_finish_date: date
    plan_end: Optional[date] = None
    delay_days: Optional[int] = None
    status: str
    critical: bool = False
    rate_per_day: Optional[float] = None
    weight: float = 1.0


class ProgressForecastResponse(BaseModel):
    """项目进度预测"""

    project_id: int
    project_name: str
    current_progress: float
    predicted_completion_date: date
    planned_completion_date: Optional[date] = None
    predicted_delay_days: int
    forecast_horizon_days: int
    confidence: str
    expected_progress_next_7d: float
    expected_progress_next_14d: float
    tasks: List[TaskForecastItem]


class DependencyIssue(BaseModel):
    """依赖问题描述"""

    issue_type: str
    severity: str
    task_id: Optional[int] = None
    task_name: Optional[str] = None
    detail: str


class DependencyCheckResponse(BaseModel):
    """依赖检查响应"""

    project_id: int
    project_name: str
    has_cycle: bool
    cycle_paths: List[List[str]]
    issues: List[DependencyIssue]


class ProgressReportListResponse(PaginatedResponse):
    """进度报告列表响应"""
    items: List[ProgressReportResponse]


# ==================== 进度汇总 ====================

class ProgressSummaryResponse(BaseModel):
    """进度汇总响应"""
    project_id: int
    project_name: str
    overall_progress: float = Field(description="整体进度百分比")
    stage_progress: dict = Field(default={}, description="各阶段进度")
    task_count: int = Field(description="任务总数")
    completed_count: int = Field(description="已完成任务数")
    in_progress_count: int = Field(description="进行中任务数")
    blocked_count: int = Field(description="阻塞任务数")
    overdue_count: int = Field(description="逾期任务数")
    delay_days: Optional[int] = Field(default=None, description="延期天数")


class MachineProgressSummaryResponse(BaseModel):
    """机台进度汇总响应"""
    machine_id: int
    machine_name: str
    machine_code: str
    overall_progress: float
    task_count: int
    completed_count: int
    in_progress_count: int
    blocked_count: int


# ==================== 甘特图数据 ====================

class GanttTaskItem(BaseModel):
    """甘特图任务项"""
    id: int
    name: str
    start: date
    end: date
    progress: int
    status: str
    dependencies: List[int] = Field(default=[], description="依赖的任务ID列表")
    owner: Optional[str] = None


class GanttDataResponse(BaseModel):
    """甘特图数据响应"""
    project_id: int
    project_name: str
    tasks: List[GanttTaskItem]


# ==================== 进度看板 ====================

class ProgressBoardColumn(BaseModel):
    """看板列"""
    status: str
    status_name: str
    tasks: List[TaskResponse]


class ProgressBoardResponse(BaseModel):
    """进度看板响应"""
    project_id: int
    project_name: str
    columns: List[ProgressBoardColumn]
    summary: dict = Field(default={}, description="汇总统计")


# ==================== 任务依赖 ====================

class TaskDependencyCreate(BaseModel):
    """创建任务依赖"""
    depends_on_task_id: int = Field(description="依赖的任务ID")
    dependency_type: str = Field(default="FS", description="依赖类型：FS/SS/FF/SF")
    lag_days: int = Field(default=0, description="滞后天数")


class TaskDependencyResponse(BaseSchema):
    """任务依赖响应"""
    id: int
    task_id: int
    depends_on_task_id: int
    dependency_type: str
    lag_days: int
    depends_on_task_name: Optional[str] = None


# ==================== 任务分配 ====================

class TaskAssigneeUpdate(BaseModel):
    """更新任务负责人"""
    owner_id: int = Field(description="负责人ID")


class ProgressLogResponse(BaseModel):
    """进度日志响应"""
    id: int
    task_id: int
    progress_percent: Optional[int] = None
    update_note: Optional[str] = None
    updated_by: Optional[int] = None
    updated_by_name: Optional[str] = None
    updated_at: datetime


class ProgressLogListResponse(BaseModel):
    """进度日志列表响应"""
    items: List[ProgressLogResponse]
    total: int


class BatchTaskProgressUpdate(BaseModel):
    """批量更新任务进度"""
    task_ids: List[int] = Field(description="任务ID列表")
    progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    update_note: Optional[str] = Field(default=None, description="更新说明")


class BatchTaskAssigneeUpdate(BaseModel):
    """批量分配任务负责人"""
    task_ids: List[int] = Field(description="任务ID列表")
    owner_id: int = Field(description="负责人ID")


# ==================== 里程碑统计 ====================

class MilestoneRateResponse(BaseModel):
    """里程碑达成率响应"""
    project_id: int
    project_name: str
    total_milestones: int
    completed_milestones: int
    completion_rate: float = Field(description="达成率百分比")
    overdue_milestones: int
    pending_milestones: int
    milestones: List[dict] = Field(default=[], description="里程碑详情列表")


# ==================== 延期原因统计 ====================

class DelayReasonItem(BaseModel):
    """延期原因项"""
    reason: str = Field(description="延期原因")
    count: int = Field(description="数量")
    percentage: float = Field(description="占比百分比")


class DelayReasonsResponse(BaseModel):
    """延期原因统计响应"""
    project_id: Optional[int] = None
    total_delayed_tasks: int
    reasons: List[DelayReasonItem] = Field(description="延期原因列表（Top N）")


# ==================== 计划基线 ====================

class BaselineCreate(BaseModel):
    """创建计划基线"""
    baseline_no: Optional[str] = Field(default=None, max_length=10, description="基线编号（可选，默认自动生成）")
    description: Optional[str] = Field(default=None, description="基线说明")


class BaselineResponse(TimestampSchema):
    """计划基线响应"""
    id: int
    project_id: int
    baseline_no: str
    created_by: Optional[int] = None
    task_count: Optional[int] = Field(default=None, description="基线任务数量")


class BaselineListResponse(PaginatedResponse):
    """计划基线列表响应"""
    items: List[BaselineResponse]
