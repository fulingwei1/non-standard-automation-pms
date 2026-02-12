# -*- coding: utf-8 -*-
"""
workstation Schemas

包含workstation相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from typing import Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ==================== 工位管理 ====================

class WorkstationCreate(BaseModel):
    """创建工位"""
    workstation_code: str = Field(max_length=50, description="工位编码")
    workstation_name: str = Field(max_length=100, description="工位名称")
    equipment_id: Optional[int] = Field(default=None, description="关联设备ID")
    description: Optional[str] = Field(default=None, description="描述")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class WorkstationUpdate(BaseModel):
    """更新工位"""
    workstation_name: Optional[str] = None
    equipment_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkstationResponse(TimestampSchema):
    """工位响应"""
    id: int
    workstation_code: str
    workstation_name: str
    workshop_id: int
    workshop_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    status: str
    current_worker_id: Optional[int] = None
    current_work_order_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool


class WorkstationStatusResponse(BaseModel):
    """工位状态响应"""
    workstation_id: int
    workstation_code: str
    workstation_name: str
    status: str
    current_worker_id: Optional[int] = None
    current_worker_name: Optional[str] = None
    current_work_order_id: Optional[int] = None
    current_work_order_no: Optional[str] = None
    is_available: bool


