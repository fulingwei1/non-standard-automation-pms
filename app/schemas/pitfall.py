# -*- coding: utf-8 -*-
"""
踩坑库 Pydantic Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class PitfallCreate(BaseModel):
    """创建踩坑记录"""

    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(..., description="问题描述")
    solution: Optional[str] = Field(None, description="解决方案")

    # 多维度分类
    stage: Optional[str] = Field(None, description="阶段：S1-S9")
    equipment_type: Optional[str] = Field(None, description="设备类型")
    problem_type: Optional[str] = Field(None, description="问题类型")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    # 选填字段
    root_cause: Optional[str] = Field(None, description="根因分析")
    impact: Optional[str] = Field(None, description="影响范围")
    prevention: Optional[str] = Field(None, description="预防措施")
    cost_impact: Optional[Decimal] = Field(None, description="成本影响（元）")
    schedule_impact: Optional[int] = Field(None, description="工期影响（天）")

    # 来源追溯
    source_type: Optional[str] = Field(None, description="来源类型")
    source_project_id: Optional[int] = Field(None, description="来源项目ID")
    source_ecn_id: Optional[int] = Field(None, description="关联ECN ID")
    source_issue_id: Optional[int] = Field(None, description="关联Issue ID")

    # 权限
    is_sensitive: bool = Field(False, description="是否敏感")
    sensitive_reason: Optional[str] = Field(None, description="敏感原因")
    visible_to: Optional[List[int]] = Field(None, description="可见范围")


class PitfallUpdate(BaseModel):
    """更新踩坑记录"""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    solution: Optional[str] = None

    stage: Optional[str] = None
    equipment_type: Optional[str] = None
    problem_type: Optional[str] = None
    tags: Optional[List[str]] = None

    root_cause: Optional[str] = None
    impact: Optional[str] = None
    prevention: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    schedule_impact: Optional[int] = None

    is_sensitive: Optional[bool] = None
    sensitive_reason: Optional[str] = None
    visible_to: Optional[List[int]] = None

    status: Optional[str] = None


class PitfallResponse(BaseModel):
    """踩坑记录响应"""

    id: int
    pitfall_no: str
    title: str
    description: str
    solution: Optional[str]

    stage: Optional[str]
    equipment_type: Optional[str]
    problem_type: Optional[str]
    tags: Optional[List[str]]

    root_cause: Optional[str]
    impact: Optional[str]
    prevention: Optional[str]
    cost_impact: Optional[Decimal]
    schedule_impact: Optional[int]

    source_type: Optional[str]
    source_project_id: Optional[int]

    is_sensitive: bool
    status: str
    verified: bool
    verify_count: int

    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PitfallListItem(BaseModel):
    """踩坑列表项（精简）"""

    id: int
    pitfall_no: str
    title: str
    stage: Optional[str]
    equipment_type: Optional[str]
    problem_type: Optional[str]
    tags: Optional[List[str]]
    status: str
    verified: bool
    verify_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
