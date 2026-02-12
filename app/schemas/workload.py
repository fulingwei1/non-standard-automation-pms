# -*- coding: utf-8 -*-
"""
资源排程与负荷管理 Schema
"""
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UserWorkloadSummary(BaseModel):
    """用户负荷汇总"""
    total_assigned_hours: float = Field(description="总分配工时")
    standard_hours: float = Field(description="标准工时（月标准工时）")
    allocation_rate: float = Field(description="分配率（%）")
    actual_hours: float = Field(description="实际工时")
    efficiency: float = Field(description="效率（%）")


class ProjectWorkloadItem(BaseModel):
    """项目负荷项"""
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    assigned_hours: float
    actual_hours: float
    task_count: int


class DailyWorkloadItem(BaseModel):
    """每日负荷项"""
    date: date
    assigned: float
    actual: float


class TaskWorkloadItem(BaseModel):
    """任务负荷项"""
    task_id: int
    task_name: str
    project_code: Optional[str] = None
    plan_hours: float
    actual_hours: float
    progress: int
    deadline: Optional[date] = None


class UserWorkloadResponse(BaseModel):
    """用户负荷详情响应"""
    user_id: int
    user_name: str
    dept_name: Optional[str] = None
    period: Dict[str, str] = Field(description="统计周期")
    summary: UserWorkloadSummary
    by_project: List[ProjectWorkloadItem] = []
    daily_load: List[DailyWorkloadItem] = []
    tasks: List[TaskWorkloadItem] = []


class TeamWorkloadItem(BaseModel):
    """团队负荷项"""
    user_id: int
    user_name: str
    dept_name: Optional[str] = None
    role: Optional[str] = None
    assigned_hours: float
    standard_hours: float
    allocation_rate: float
    task_count: int
    overdue_count: int = 0


class TeamWorkloadResponse(BaseModel):
    """团队负荷响应"""
    items: List[TeamWorkloadItem]


class WorkloadHeatmapResponse(BaseModel):
    """负荷热力图响应"""
    users: List[str] = Field(description="用户列表")
    weeks: List[str] = Field(description="周列表")
    data: List[List[float]] = Field(description="负荷数据矩阵")


class AvailableResourceItem(BaseModel):
    """可用资源项"""
    user_id: int
    user_name: str
    dept_name: Optional[str] = None
    role: Optional[str] = None
    available_hours: float
    skills: List[str] = []


class AvailableResourceResponse(BaseModel):
    """可用资源响应"""
    items: List[AvailableResourceItem]


class WorkloadDashboardSummary(BaseModel):
    """负荷看板汇总"""
    total_users: int = 0
    overloaded_users: int = 0
    normal_users: int = 0
    underloaded_users: int = 0
    total_assigned_hours: float = 0.0
    total_actual_hours: float = 0.0
    average_allocation_rate: float = 0.0


class WorkloadDashboardResponse(BaseModel):
    """负荷看板响应"""
    summary: WorkloadDashboardSummary
    team_workload: List[TeamWorkloadItem] = []



