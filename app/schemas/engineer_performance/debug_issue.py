# -*- coding: utf-8 -*-
"""
debug_issue Schemas

包含debug_issue相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 调试问题 Schemas ====================

class MechanicalDebugIssueBase(BaseModel):
    """机械调试问题基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    issue_description: str = Field(..., description="问题描述")
    severity: Optional[str] = Field(None, description="严重程度")
    root_cause: Optional[str] = Field(None, description="根本原因")
    affected_part: Optional[str] = Field(None, description="受影响零件")


class MechanicalDebugIssueCreate(MechanicalDebugIssueBase):
    """创建机械调试问题"""
    responsible_id: int = Field(..., description="责任人ID")
    found_date: Optional[date] = Field(None, description="发现日期")


class MechanicalDebugIssueUpdate(BaseModel):
    """更新机械调试问题"""
    status: Optional[str] = None
    resolved_date: Optional[date] = None
    resolution: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    time_impact_hours: Optional[Decimal] = None


class MechanicalDebugIssueResponse(MechanicalDebugIssueBase):
    """机械调试问题响应"""
    id: int
    responsible_id: int
    responsible_name: Optional[str] = None
    reporter_id: Optional[int] = None
    issue_code: Optional[str] = None
    status: str
    found_date: Optional[date] = None
    resolved_date: Optional[date] = None
    resolution: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    time_impact_hours: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


