# -*- coding: utf-8 -*-
"""
bug_record Schemas

包含bug_record相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== Bug记录 Schemas ====================

class TestBugRecordBase(BaseModel):
    """Bug记录基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    title: str = Field(..., max_length=200, description="标题")
    description: Optional[str] = Field(None, description="描述")
    severity: Optional[str] = Field(None, description="严重程度")
    bug_type: Optional[str] = Field(None, description="Bug类型")
    found_stage: Optional[str] = Field(None, description="发现阶段")
    priority: Optional[str] = Field('normal', description="优先级")


class TestBugRecordCreate(TestBugRecordBase):
    """创建Bug记录"""
    assignee_id: int = Field(..., description="处理人ID")
    found_time: Optional[datetime] = Field(None, description="发现时间")


class TestBugRecordUpdate(BaseModel):
    """更新Bug记录"""
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    resolved_time: Optional[datetime] = None
    fix_duration_hours: Optional[Decimal] = None
    resolution: Optional[str] = None


class TestBugRecordResponse(TestBugRecordBase):
    """Bug记录响应"""
    id: int
    bug_code: Optional[str] = None
    assignee_id: int
    assignee_name: Optional[str] = None
    reporter_id: Optional[int] = None
    reporter_name: Optional[str] = None
    status: str
    found_time: Optional[datetime] = None
    resolved_time: Optional[datetime] = None
    fix_duration_hours: Optional[Decimal] = None
    resolution: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


