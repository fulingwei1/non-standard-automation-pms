# -*- coding: utf-8 -*-
"""
工时管理 Schema
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema, PaginatedResponse


# ==================== 工时记录 ====================

class TimesheetCreate(BaseModel):
    """创建工时记录"""
    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
    task_id: Optional[int] = None
    work_date: date = Field(description="工作日期")
    work_hours: Decimal = Field(gt=0, le=24, description="工作小时数")
    work_type: str = Field(default="NORMAL", description="工作类型：NORMAL/OVERTIME/LEAVE")
    description: Optional[str] = None
    is_billable: bool = Field(default=True, description="是否可计费")


class TimesheetUpdate(BaseModel):
    """更新工时记录"""
    work_date: Optional[date] = None
    work_hours: Optional[Decimal] = Field(None, gt=0, le=24)
    work_type: Optional[str] = None
    description: Optional[str] = None
    is_billable: Optional[bool] = None


class TimesheetResponse(TimestampSchema):
    """工时记录响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[int] = None
    task_name: Optional[str] = None
    work_date: date
    work_hours: Decimal
    work_type: str
    description: Optional[str] = None
    is_billable: bool = True
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class TimesheetListResponse(PaginatedResponse):
    """工时记录列表响应"""
    items: List[TimesheetResponse]


class TimesheetBatchCreate(BaseModel):
    """批量创建工时记录"""
    timesheets: List[TimesheetCreate] = Field(description="工时记录列表")


# ==================== 周工时表 ====================

class WeekTimesheetResponse(BaseModel):
    """周工时表响应"""
    week_start: date
    week_end: date
    total_hours: Decimal
    by_date: Dict[str, Decimal] = Field(description="按日期统计")
    by_project: Dict[str, Decimal] = Field(description="按项目统计")
    timesheets: List[TimesheetResponse]


# ==================== 月度汇总 ====================

class MonthSummaryResponse(BaseModel):
    """月度汇总响应"""
    year: int
    month: int
    total_hours: Decimal
    billable_hours: Decimal
    non_billable_hours: Decimal
    by_project: Dict[str, Decimal]
    by_work_type: Dict[str, Decimal]
    by_date: Dict[str, Decimal]


# ==================== 工时统计 ====================

class TimesheetStatisticsResponse(BaseModel):
    """工时统计分析响应"""
    total_hours: Decimal
    billable_hours: Decimal
    by_user: Dict[str, Decimal]
    by_project: Dict[str, Decimal]
    by_date: Dict[str, Decimal]
    by_work_type: Dict[str, Decimal]
