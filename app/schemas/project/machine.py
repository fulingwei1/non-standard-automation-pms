# -*- coding: utf-8 -*-
"""
设备管理 Schema
包含设备的创建、更新、响应模型
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from ..common import TimestampSchema

ZERO_DECIMAL = Decimal("0")


class MachineCreate(BaseModel):
    """创建设备"""

    machine_code: Optional[str] = Field(
        None, max_length=50, description="设备编码（可选，不提供则自动生成）"
    )
    machine_name: str = Field(max_length=200, description="设备名称")
    project_id: Optional[int] = Field(None, description="项目ID（可选，通常从路径中获取）")
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
    progress_pct: Decimal = ZERO_DECIMAL
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_nulls(cls, value):
        if isinstance(value, dict):
            data = dict(value)
        elif hasattr(value, "id"):
            fields = (
                "id",
                "machine_code",
                "machine_name",
                "machine_no",
                "project_id",
                "project_name",
                "machine_type",
                "stage",
                "status",
                "health",
                "progress_pct",
                "planned_start_date",
                "planned_end_date",
                "actual_start_date",
                "actual_end_date",
                "created_at",
                "updated_at",
            )
            data = {field: getattr(value, field, None) for field in fields}
        else:
            return value

        data["machine_no"] = data.get("machine_no") or 1
        data["stage"] = data.get("stage") or "S1"
        data["status"] = data.get("status") or "ST01"
        data["health"] = data.get("health") or "H1"
        if data.get("progress_pct") is None:
            data["progress_pct"] = ZERO_DECIMAL
        return data
