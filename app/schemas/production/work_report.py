# -*- coding: utf-8 -*-
"""
work_report Schemas

包含work_report相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..common import PaginatedResponse, TimestampSchema

# ==================== 报工 ====================


class WorkReportStartRequest(BaseModel):
    """开工报告请求"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    work_order_id: int = Field(description="工单ID")
    worker_id: Optional[int] = Field(default=None, description="工人ID，兼容旧请求；可省略")
    report_note: Optional[str] = Field(default=None, description="报工说明")

    @model_validator(mode="before")
    @classmethod
    def _normalize_worker_id(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if payload.get("worker_id") is None and payload.get("assigned_to") is not None:
                payload["worker_id"] = payload["assigned_to"]
            return payload
        return data


class WorkReportProgressRequest(BaseModel):
    """进度上报请求"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    work_order_id: int = Field(description="工单ID")
    worker_id: Optional[int] = Field(default=None, description="工人ID，兼容旧请求；可省略")
    progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    work_hours: Optional[Decimal] = Field(default=None, description="本次工时")
    report_note: Optional[str] = Field(default=None, description="报工说明")

    @model_validator(mode="before")
    @classmethod
    def _normalize_worker_id(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if payload.get("worker_id") is None and payload.get("assigned_to") is not None:
                payload["worker_id"] = payload["assigned_to"]
            return payload
        return data


class WorkReportCompleteRequest(BaseModel):
    """完工报告请求"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    work_order_id: int = Field(description="工单ID")
    worker_id: Optional[int] = Field(default=None, description="工人ID，兼容旧请求；可省略")
    completed_qty: int = Field(description="完成数量")
    qualified_qty: int = Field(description="合格数量")
    defect_qty: Optional[int] = Field(default=0, description="不良数量")
    work_hours: Optional[Decimal] = Field(default=None, description="本次工时")
    report_note: Optional[str] = Field(default=None, description="报工说明")

    @model_validator(mode="before")
    @classmethod
    def _normalize_worker_id(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if payload.get("worker_id") is None and payload.get("assigned_to") is not None:
                payload["worker_id"] = payload["assigned_to"]
            return payload
        return data


class WorkReportResponse(TimestampSchema):
    """报工响应"""

    id: int
    report_no: str
    work_order_id: int
    work_order_no: Optional[str] = None
    worker_id: int
    worker_name: Optional[str] = None
    report_type: str
    report_time: datetime
    progress_percent: Optional[int] = None
    work_hours: Optional[float] = None
    completed_qty: Optional[int] = None
    qualified_qty: Optional[int] = None
    defect_qty: Optional[int] = None
    status: str
    report_note: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class WorkReportListResponse(PaginatedResponse):
    """报工列表响应"""

    items: List[WorkReportResponse]
