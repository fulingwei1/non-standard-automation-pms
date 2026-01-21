# -*- coding: utf-8 -*-
"""
节点子任务 Schemas

包含节点子任务相关的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 节点子任务 Schemas ====================

class NodeTaskBase(BaseModel):
    """节点子任务基础"""
    task_name: str = Field(..., max_length=200, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="预计工时(小时)")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: str = Field(default="NORMAL", description="优先级: LOW/NORMAL/HIGH/URGENT")
    tags: Optional[str] = Field(default=None, max_length=200, description="标签(逗号分隔)")


class NodeTaskCreate(NodeTaskBase):
    """创建节点子任务"""
    node_instance_id: int = Field(..., description="所属节点实例ID")
    task_code: Optional[str] = Field(default=None, max_length=30, description="任务编码(不传则自动生成)")
    assignee_id: Optional[int] = Field(default=None, description="执行人ID")


class NodeTaskUpdate(BaseModel):
    """更新节点子任务"""
    task_name: Optional[str] = Field(default=None, max_length=200, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="预计工时")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: Optional[str] = Field(default=None, description="优先级")
    tags: Optional[str] = Field(default=None, description="标签")
    assignee_id: Optional[int] = Field(default=None, description="执行人ID")
    remark: Optional[str] = Field(default=None, description="备注")


class NodeTaskComplete(BaseModel):
    """完成节点子任务请求"""
    actual_hours: Optional[int] = Field(default=None, ge=0, description="实际工时")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    remark: Optional[str] = Field(default=None, description="备注")


class NodeTaskResponse(NodeTaskBase):
    """节点子任务响应"""
    id: int
    node_instance_id: int
    task_code: str
    sequence: int
    status: str
    actual_hours: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    assignee_id: Optional[int] = None
    completed_by: Optional[int] = None
    completed_at: Optional[datetime] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchCreateTasksRequest(BaseModel):
    """批量创建任务请求"""
    tasks: List[NodeTaskBase] = Field(..., description="任务列表")


class ReorderTasksRequest(BaseModel):
    """重排任务顺序请求"""
    task_ids: List[int] = Field(..., description="按新顺序排列的任务ID列表")


class NodeTaskProgressResponse(BaseModel):
    """节点任务进度响应"""
    total: int = Field(description="总任务数")
    completed: int = Field(description="已完成数")
    in_progress: int = Field(description="进行中数")
    pending: int = Field(description="待开始数")
    skipped: int = Field(description="已跳过数")
    progress_pct: float = Field(description="完成百分比")
    total_estimated_hours: int = Field(description="总预计工时")
    total_actual_hours: int = Field(description="总实际工时")


class AssignNodeRequest(BaseModel):
    """分配节点负责人请求"""
    assignee_id: int = Field(..., description="负责人ID")
    auto_complete_on_tasks: bool = Field(default=True, description="子任务全部完成时是否自动完成节点")


