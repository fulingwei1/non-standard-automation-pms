# -*- coding: utf-8 -*-
"""
工程师进度管理 - Pydantic Schemas
包含：我的项目、任务创建/更新、进度更新、完成证明、延期报告
"""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ==================== 基础响应模型 ====================

class TaskStatsResponse(BaseModel):
    """任务统计"""
    total_tasks: int = Field(0, description="总任务数")
    pending_tasks: int = Field(0, description="待接收任务数")
    in_progress_tasks: int = Field(0, description="进行中任务数")
    completed_tasks: int = Field(0, description="已完成任务数")
    overdue_tasks: int = Field(0, description="逾期任务数")
    delayed_tasks: int = Field(0, description="延期任务数")
    pending_approval_tasks: int = Field(0, description="待审批任务数")


# ==================== 我的项目列表 ====================

class MyProjectResponse(BaseModel):
    """工程师-我的项目响应"""
    project_id: int = Field(..., description="项目ID")
    project_code: str = Field(..., description="项目编号")
    project_name: str = Field(..., description="项目名称")
    customer_name: Optional[str] = Field(None, description="客户名称")

    stage: str = Field(..., description="当前阶段")
    status: str = Field(..., description="项目状态")
    health: str = Field(..., description="健康度")
    progress_pct: float = Field(0, description="进度百分比")

    my_roles: List[str] = Field(default_factory=list, description="我的角色列表")
    my_allocation_pct: int = Field(100, description="我的分配比例")

    task_stats: TaskStatsResponse = Field(..., description="任务统计")

    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")

    model_config = ConfigDict(from_attributes=True)


class MyProjectListResponse(BaseModel):
    """我的项目列表响应"""
    items: List[MyProjectResponse]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ==================== 任务创建与更新 ====================

class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    project_id: int = Field(..., description="项目ID")
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")

    task_importance: str = Field('GENERAL', description="任务重要性：IMPORTANT/GENERAL")
    justification: Optional[str] = Field(None, description="任务必要性说明（IMPORTANT任务必填）")

    wbs_code: Optional[str] = Field(None, description="WBS编码")
    plan_start_date: Optional[date] = Field(None, description="计划开始日期")
    plan_end_date: Optional[date] = Field(None, description="计划结束日期")
    deadline: Optional[datetime] = Field(None, description="截止时间")

    estimated_hours: Optional[Decimal] = Field(None, description="预估工时")
    priority: str = Field('MEDIUM', description="优先级：URGENT/HIGH/MEDIUM/LOW")

    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, description="分类")


class TaskUpdateRequest(BaseModel):
    """任务更新请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")

    plan_start_date: Optional[date] = Field(None, description="计划开始日期")
    plan_end_date: Optional[date] = Field(None, description="计划结束日期")
    deadline: Optional[datetime] = Field(None, description="截止时间")

    estimated_hours: Optional[Decimal] = Field(None, description="预估工时")
    priority: Optional[str] = Field(None, description="优先级")

    tags: Optional[List[str]] = Field(None, description="标签列表")


class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    task_code: str
    title: str
    description: Optional[str] = None
    task_type: str

    source_type: Optional[str] = None
    source_id: Optional[int] = None
    parent_task_id: Optional[int] = None

    project_id: Optional[int] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    wbs_code: Optional[str] = None

    assignee_id: int
    assignee_name: Optional[str] = None
    assigner_id: Optional[int] = None
    assigner_name: Optional[str] = None

    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    deadline: Optional[datetime] = None

    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None

    status: str
    progress: int = 0
    priority: str
    is_urgent: bool = False

    # 审批相关
    approval_required: bool = False
    approval_status: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    task_importance: str = 'GENERAL'

    # 延期相关
    is_delayed: bool = False
    delay_reason: Optional[str] = None
    new_completion_date: Optional[date] = None

    # 完成证明
    completion_note: Optional[str] = None
    proof_count: int = Field(0, description="完成证明数量")

    tags: Optional[List[str]] = None
    category: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 进度更新 ====================

class ProgressUpdateRequest(BaseModel):
    """进度更新请求"""
    progress: int = Field(..., ge=0, le=100, description="进度百分比(0-100)")
    actual_hours: Optional[Decimal] = Field(None, ge=0, description="实际工时")
    progress_note: Optional[str] = Field(None, description="进度说明")


class ProgressUpdateResponse(BaseModel):
    """进度更新响应"""
    task_id: int
    progress: int
    actual_hours: Optional[Decimal]
    status: str
    project_progress_updated: bool = Field(False, description="项目进度是否已更新")
    stage_progress_updated: bool = Field(False, description="阶段进度是否已更新")


# ==================== 任务完成 ====================

class TaskCompleteRequest(BaseModel):
    """任务完成请求"""
    completion_note: str = Field(..., min_length=1, description="完成说明")
    skip_proof_validation: bool = Field(False, description="跳过证明材料验证")


class TaskCompleteResponse(BaseModel):
    """任务完成响应"""
    task_id: int
    status: str
    progress: int
    actual_end_date: date
    completion_note: str
    proof_count: int = Field(0, description="完成证明数量")


# ==================== 完成证明上传 ====================

class ProofUploadResponse(BaseModel):
    """证明上传响应"""
    id: int
    task_id: int
    proof_type: str
    file_category: Optional[str] = None
    file_name: str
    file_size: int
    file_type: Optional[str] = None
    description: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskProofListResponse(BaseModel):
    """任务证明列表响应"""
    task_id: int
    proofs: List[ProofUploadResponse]
    total_count: int


# ==================== 延期报告 ====================

class DelayReportRequest(BaseModel):
    """延期报告请求"""
    delay_reason: str = Field(..., min_length=10, description="延期原因（详细说明）")
    delay_responsibility: str = Field(..., description="延期责任归属")
    delay_impact_scope: str = Field(..., description="延期影响范围：LOCAL/PROJECT/MULTI_PROJECT")

    schedule_impact_days: int = Field(..., ge=1, description="计划影响天数")
    cost_impact: Optional[Decimal] = Field(None, ge=0, description="成本影响(元)")
    new_completion_date: date = Field(..., description="新的预计完成日期")

    root_cause_analysis: Optional[str] = Field(None, description="根本原因分析")
    preventive_measures: Optional[str] = Field(None, description="预防措施")


class DelayReportResponse(BaseModel):
    """延期报告响应"""
    task_id: int
    exception_event_id: int = Field(..., description="异常事件ID")
    delay_visible_to: List[str] = Field(default_factory=list, description="可见人员角色列表")
    notifications_sent_count: int = Field(0, description="已发送通知数量")
    health_status_updated: bool = Field(False, description="项目健康度是否已更新")


# ==================== 任务审批（PM端） ====================

class TaskApprovalRequest(BaseModel):
    """任务审批请求"""
    approval_note: Optional[str] = Field(None, description="审批意见")


class TaskRejectionRequest(BaseModel):
    """任务拒绝请求"""
    rejection_reason: str = Field(..., min_length=5, description="拒绝原因")


class TaskApprovalResponse(BaseModel):
    """任务审批响应"""
    task_id: int
    approval_status: str
    approved_by: int
    approved_at: datetime
    approval_note: Optional[str] = None


# ==================== 跨部门进度视图 ====================

class MemberProgressSummary(BaseModel):
    """人员进度汇总"""
    name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int = 0
    progress_pct: float = 0


class DepartmentProgressSummary(BaseModel):
    """部门进度汇总"""
    department_id: int
    department_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    delayed_tasks: int
    progress_pct: float
    members: List[MemberProgressSummary]


class StageProgressSummary(BaseModel):
    """阶段进度汇总"""
    progress: float
    status: str


class ActiveDelayInfo(BaseModel):
    """活跃延期信息"""
    task_id: int
    task_title: str
    assignee_name: str
    department: str
    delay_days: int
    impact_scope: str
    new_completion_date: date
    delay_reason: str
    reported_at: datetime


class ProjectProgressVisibilityResponse(BaseModel):
    """项目进度可见性响应"""
    project_id: int
    project_name: str
    overall_progress: float

    department_progress: List[DepartmentProgressSummary]
    stage_progress: dict[str, StageProgressSummary]

    active_delays: List[ActiveDelayInfo]

    last_updated_at: datetime


# ==================== 分页响应 ====================

class TaskListResponse(BaseModel):
    """任务列表响应"""
    items: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1
