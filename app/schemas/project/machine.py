# -*- coding: utf-8 -*-
"""
设备管理 Schema
包含设备的创建、更新、响应模型
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class MachineCreate(BaseModel):
    """创建设备"""

    machine_code: Optional[str] = Field(None, max_length=50, description="设备编码（可选，不提供则自动生成）")
    machine_name: str = Field(max_length=200, description="设备名称")
    project_id: int = Field(description="项目ID")
    machine_no: Optional[int] = 1
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    remark: Optional[str] = None


class MachineUpdate(BaseModel):
    """更新设备"""

    machine_name: Optional[str] = None
    machine_no: Optional[int] = None
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    fat_date: Optional[date] = None
    fat_result: Optional[str] = None
    sat_date: Optional[date] = None
    sat_result: Optional[str] = None
    ship_date: Optional[date] = None
    ship_address: Optional[str] = None
    tracking_no: Optional[str] = None
    remark: Optional[str] = None


class MachineResponse(TimestampSchema):
    """设备响应"""

    id: int
    machine_code: str
    machine_name: str
    machine_no: int
    project_id: int
    project_name: Optional[str] = None
    machine_type: Optional[str] = None
    stage: str = "S1"
    status: str = "ST01"
    health: str = "H1"
    progress_pct: Decimal = 0
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    class Config:
        from_attributes = True
