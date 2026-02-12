# -*- coding: utf-8 -*-
"""
workshop Schemas

包含workshop相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import PaginatedResponse, TimestampSchema


# ==================== 车间管理 ====================

class WorkshopCreate(BaseModel):
    """创建车间"""
    workshop_code: str = Field(max_length=50, description="车间编码")
    workshop_name: str = Field(max_length=100, description="车间名称")
    workshop_type: str = Field(description="车间类型：MACHINING/ASSEMBLY/DEBUGGING等")
    manager_id: Optional[int] = Field(default=None, description="车间主管ID")
    location: Optional[str] = Field(default=None, max_length=200, description="车间位置")
    capacity_hours: Optional[Decimal] = Field(default=None, description="日产能(工时)")
    description: Optional[str] = Field(default=None, description="描述")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class WorkshopUpdate(BaseModel):
    """更新车间"""
    workshop_name: Optional[str] = None
    workshop_type: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    capacity_hours: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkshopResponse(TimestampSchema):
    """车间响应"""
    id: int
    workshop_code: str
    workshop_name: str
    workshop_type: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    location: Optional[str] = None
    capacity_hours: Optional[float] = None
    description: Optional[str] = None
    is_active: bool


class WorkshopListResponse(PaginatedResponse):
    """车间列表响应"""
    items: List[WorkshopResponse]


