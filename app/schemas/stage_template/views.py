# -*- coding: utf-8 -*-
"""
视图 Schemas

包含流水线视图、时间轴视图、分解树视图的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 流水线视图 Schemas ====================

class ProjectStageOverview(BaseModel):
    """项目阶段概览（流水线视图用）"""
    project_id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    current_stage_code: Optional[str] = None
    current_stage_name: Optional[str] = None
    progress_pct: float = Field(default=0, description="整体进度百分比")
    health_status: str = Field(default="H1", description="健康状态")
    stages: List[StageProgress] = Field(default=[], description="阶段列表")


class PipelineStatistics(BaseModel):
    """流水线统计数据"""
    total_projects: int = Field(default=0, description="总项目数")
    in_progress_count: int = Field(default=0, description="进行中项目数")
    completed_count: int = Field(default=0, description="已完成项目数")
    delayed_count: int = Field(default=0, description="延期项目数")
    blocked_count: int = Field(default=0, description="受阻项目数")
    # 按阶段分类统计
    by_category: Dict[str, int] = Field(default={}, description="按阶段分类统计")
    # 按当前阶段统计
    by_current_stage: Dict[str, int] = Field(default={}, description="按当前阶段统计")


class PipelineViewResponse(BaseModel):
    """流水线视图响应"""
    statistics: PipelineStatistics
    projects: List[ProjectStageOverview]
    stage_definitions: List[StageDefinitionResponse] = Field(
        default=[], description="阶段定义列表（用于表头）"
    )


# ==================== 时间轴视图 Schemas ====================

class TimelineNode(BaseModel):
    """时间轴节点"""
    id: int
    node_code: str
    node_name: str
    node_type: str
    status: str
    progress: int = 0
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    assignee_name: Optional[str] = None
    dependency_ids: List[int] = Field(default=[], description="依赖节点ID")


class TimelineStage(BaseModel):
    """时间轴阶段"""
    id: int
    stage_code: str
    stage_name: str
    category: str
    status: str
    is_milestone: bool = False
    is_parallel: bool = False
    progress: int = 0
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    nodes: List[TimelineNode] = Field(default=[], description="节点列表")


class TimelineViewResponse(BaseModel):
    """时间轴视图响应"""
    project_id: int
    project_code: str
    project_name: str
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    overall_progress: float = 0
    stages: List[TimelineStage] = Field(default=[], description="阶段列表")


# ==================== 分解树视图 Schemas ====================

class TreeTask(BaseModel):
    """分解树任务节点"""
    id: int
    task_code: str
    task_name: str
    status: str
    priority: str = "NORMAL"
    assignee_name: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    progress_pct: float = 0


class TreeNode(BaseModel):
    """分解树节点"""
    id: int
    node_code: str
    node_name: str
    node_type: str
    status: str
    progress: int = 0
    assignee_name: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    tasks: List[TreeTask] = Field(default=[], description="子任务列表")


class TreeStage(BaseModel):
    """分解树阶段"""
    id: int
    stage_code: str
    stage_name: str
    category: str
    status: str
    is_milestone: bool = False
    progress: int = 0
    total_nodes: int = 0
    completed_nodes: int = 0
    nodes: List[TreeNode] = Field(default=[], description="节点列表")


class TreeViewResponse(BaseModel):
    """分解树视图响应"""
    project_id: int
    project_code: str
    project_name: str
    overall_progress: float = 0
    total_stages: int = 0
    completed_stages: int = 0
    total_nodes: int = 0
    completed_nodes: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    stages: List[TreeStage] = Field(default=[], description="阶段列表")


