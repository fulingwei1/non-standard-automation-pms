# -*- coding: utf-8 -*-
"""
初始化项目阶段 Schemas

包含初始化项目阶段相关的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 初始化项目阶段 Schemas ====================

class StageAdjustment(BaseModel):
    """阶段调整配置"""
    estimated_days: Optional[int] = Field(default=None, description="调整后的预计工期")
    stage_name: Optional[str] = Field(default=None, description="调整后的阶段名称")


class NodeAdjustment(BaseModel):
    """节点调整配置"""
    estimated_days: Optional[int] = Field(default=None, description="调整后的预计工期")
    node_name: Optional[str] = Field(default=None, description="调整后的节点名称")
    is_required: Optional[bool] = Field(default=None, description="是否必需")


class InitializeProjectStagesRequest(BaseModel):
    """初始化项目阶段请求"""
    template_id: int = Field(..., description="模板ID")
    start_date: Optional[date] = Field(default=None, description="项目开始日期")
    skip_stages: Optional[List[str]] = Field(default=None, description="跳过的阶段编码列表")
    skip_nodes: Optional[List[str]] = Field(default=None, description="跳过的节点编码列表")
    stage_overrides: Optional[Dict[str, StageAdjustment]] = Field(default=None, description="阶段调整配置")
    node_overrides: Optional[Dict[str, NodeAdjustment]] = Field(default=None, description="节点调整配置")


class AddCustomNodeRequest(BaseModel):
    """添加自定义节点请求"""
    stage_instance_id: int = Field(..., description="阶段实例ID")
    node_code: str = Field(..., max_length=20, description="节点编码")
    node_name: str = Field(..., max_length=100, description="节点名称")
    node_type: str = Field(default="TASK", description="节点类型")
    completion_method: str = Field(default="MANUAL", description="完成方式")
    is_required: bool = Field(default=False, description="是否必需")
    planned_date: Optional[date] = Field(default=None, description="计划日期")
    insert_after_node_id: Optional[int] = Field(default=None, description="插入位置(在此节点之后)")


