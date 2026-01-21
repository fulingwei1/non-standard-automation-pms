# -*- coding: utf-8 -*-
"""
进度和排序 Schemas

包含进度查询和排序相关的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 进度 Schemas ====================

class StageProgress(BaseModel):
    """阶段进度信息"""
    id: int
    stage_code: str
    stage_name: str
    status: str
    sequence: int
    category: str = Field(default="execution", description="阶段分类")
    is_milestone: bool = Field(default=False, description="是否关键里程碑")
    is_parallel: bool = Field(default=False, description="是否支持并行执行")
    total_nodes: int
    completed_nodes: int
    progress_pct: float
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None


class CurrentStageInfo(BaseModel):
    """当前阶段信息"""
    id: int
    stage_code: str
    stage_name: str
    progress_pct: float


class ProjectProgressResponse(BaseModel):
    """项目进度响应"""
    total_stages: int = Field(description="总阶段数")
    completed_stages: int = Field(description="已完成阶段数")
    current_stage: Optional[CurrentStageInfo] = Field(default=None, description="当前阶段")
    total_nodes: int = Field(description="总节点数")
    completed_nodes: int = Field(description="已完成节点数")
    progress_pct: float = Field(description="整体进度百分比")
    stages: List[StageProgress] = Field(default=[], description="阶段列表")


# ==================== 排序 Schemas ====================

class ReorderStagesRequest(BaseModel):
    """重排阶段顺序请求"""
    stage_ids: List[int] = Field(..., description="按新顺序排列的阶段ID列表")


class ReorderNodesRequest(BaseModel):
    """重排节点顺序请求"""
    node_ids: List[int] = Field(..., description="按新顺序排列的节点ID列表")


class SetNodeDependenciesRequest(BaseModel):
    """设置节点依赖请求"""
    dependency_node_ids: List[int] = Field(default=[], description="依赖节点ID列表")


