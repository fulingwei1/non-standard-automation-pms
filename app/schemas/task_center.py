# -*- coding: utf-8 -*-
"""
个人任务中心 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import PaginatedResponse, TimestampSchema

# ==================== 任务概览 ====================

class TaskOverviewResponse(BaseModel):
    """任务概览统计"""
    total_tasks: int = Field(description="总任务数")
    pending_tasks: int = Field(description="待接收任务数")
    in_progress_tasks: int = Field(description="进行中任务数")
    overdue_tasks: int = Field(description="逾期任务数")
    this_week_tasks: int = Field(description="本周任务数")
    urgent_tasks: int = Field(description="紧急任务数")
    by_status: Dict[str, int] = Field(default={}, description="按状态统计")
    by_priority: Dict[str, int] = Field(default={}, description="按优先级统计")
    by_type: Dict[str, int] = Field(default={}, description="按类型统计")


# ==================== 统一任务 ====================

class TaskUnifiedCreate(BaseModel):
    """创建个人任务"""
    title: str = Field(description="任务标题")
    description: Optional[str] = None
    task_type: str = Field(default="PERSONAL", description="任务类型")
    project_id: Optional[int] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    deadline: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = None
    priority: str = Field(default="MEDIUM", description="优先级：URGENT/HIGH/MEDIUM/LOW")
    is_urgent: bool = Field(default=False)
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    category: Optional[str] = None
    reminder_enabled: bool = Field(default=True)
    reminder_before_hours: int = Field(default=24)


class TaskUnifiedUpdate(BaseModel):
    """更新任务"""
    title: Optional[str] = None
    description: Optional[str] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    deadline: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = None
    priority: Optional[str] = None
    is_urgent: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_before_hours: Optional[int] = None


class TaskUnifiedResponse(TimestampSchema):
    """任务响应"""
    id: int
    task_code: str
    title: str
    description: Optional[str] = None
    task_type: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
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
    actual_hours: Decimal = 0
    status: str
    progress: int = 0
    priority: str
    is_urgent: bool = False
    is_transferred: bool = False
    transfer_from_name: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_overdue: bool = Field(default=False, description="是否逾期")


class TaskUnifiedListResponse(PaginatedResponse):
    """任务列表响应"""
    items: List[TaskUnifiedResponse]


class TaskProgressUpdate(BaseModel):
    """更新任务进度"""
    progress: int = Field(ge=0, le=100, description="进度百分比")
    actual_hours: Optional[Decimal] = None
    note: Optional[str] = None


class TaskTransferRequest(BaseModel):
    """任务转办请求"""
    target_user_id: int = Field(description="目标用户ID")
    transfer_reason: str = Field(description="转办原因")
    notify: bool = Field(default=True, description="是否通知")


class TaskCommentCreate(BaseModel):
    """创建任务评论"""
    content: str = Field(description="评论内容")
    comment_type: str = Field(default="COMMENT", description="评论类型：COMMENT/PROGRESS/QUESTION/REPLY")
    parent_id: Optional[int] = None
    mentioned_users: Optional[List[int]] = Field(default=[], description="@的用户ID列表")


class TaskCommentResponse(BaseModel):
    """任务评论响应"""
    id: int
    task_id: int
    content: str
    comment_type: str
    parent_id: Optional[int] = None
    commenter_id: int
    commenter_name: Optional[str] = None
    mentioned_users: Optional[List[int]] = None
    created_at: datetime
    replies: Optional[List['TaskCommentResponse']] = None


# ==================== 批量操作 ====================

class BatchTaskOperation(BaseModel):
    """批量任务操作"""
    task_ids: List[int] = Field(description="任务ID列表")
    operation: str = Field(description="操作类型：complete/transfer/priority/progress/delete/start/pause/tag")
    params: Optional[Dict[str, Any]] = Field(default={}, description="操作参数")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success_count: int
    failed_count: int
    failed_tasks: List[Dict[str, Any]] = Field(default=[], description="失败的任务详情")


class BatchOperationStatistics(BaseModel):
    """批量操作统计"""
    total_operations: int
    by_operation_type: Dict[str, int]
    by_date: Dict[str, int]
    recent_operations: List[Dict[str, Any]]
