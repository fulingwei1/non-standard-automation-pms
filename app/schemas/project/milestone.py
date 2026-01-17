# -*- coding: utf-8 -*-
"""
里程碑管理 Schema
包含里程碑的创建、更新、响应模型
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class MilestoneCreate(BaseModel):
    """创建里程碑"""

    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    milestone_code: str = Field(max_length=50, description="里程碑编码")
    milestone_name: str = Field(max_length=200, description="里程碑名称")
    milestone_type: str = Field(default="CUSTOM", description="里程碑类型")
    planned_date: date = Field(description="计划日期")
    stage_code: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None


class MilestoneUpdate(BaseModel):
    """更新里程碑"""

    milestone_name: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None
    completion_note: Optional[str] = None


class MilestoneResponse(TimestampSchema):
    """里程碑响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    milestone_code: str
    milestone_name: str
    milestone_type: str
    planned_date: date
    actual_date: Optional[date] = None
    status: str = "PENDING"
    stage_code: Optional[str] = None
    owner_id: Optional[int] = None
