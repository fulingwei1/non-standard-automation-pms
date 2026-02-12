# -*- coding: utf-8 -*-
"""
production_reports Schemas

包含production_reports相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ==================== 生产报表 ====================

class ProductionDailyReportCreate(BaseModel):
    """创建生产日报"""
    report_date: date = Field(description="报告日期")
    workshop_id: Optional[int] = Field(default=None, description="车间ID(空表示全厂)")
    plan_qty: int = Field(default=0, description="计划数量")
    completed_qty: int = Field(default=0, description="完成数量")
    plan_hours: Optional[Decimal] = Field(default=0, description="计划工时")
    actual_hours: Optional[Decimal] = Field(default=0, description="实际工时")
    overtime_hours: Optional[Decimal] = Field(default=0, description="加班工时")
    should_attend: int = Field(default=0, description="应出勤人数")
    actual_attend: int = Field(default=0, description="实际出勤")
    leave_count: int = Field(default=0, description="请假人数")
    total_qty: int = Field(default=0, description="生产总数")
    qualified_qty: int = Field(default=0, description="合格数量")
    new_exception_count: int = Field(default=0, description="新增异常数")
    resolved_exception_count: int = Field(default=0, description="解决异常数")
    summary: Optional[str] = Field(default=None, description="日报总结")


class ProductionDailyReportResponse(TimestampSchema):
    """生产日报响应"""
    id: int
    report_date: date
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_qty: int
    completed_qty: int
    completion_rate: Optional[float] = None
    plan_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    efficiency: Optional[float] = None
    should_attend: int
    actual_attend: int
    leave_count: int
    total_qty: int
    qualified_qty: int
    pass_rate: Optional[float] = None
    new_exception_count: int
    resolved_exception_count: int
    summary: Optional[str] = None
    created_by: Optional[int] = None


class ProductionDashboardResponse(BaseModel):
    """生产驾驶舱响应"""
    # 总体统计
    total_workshops: int = 0
    total_workstations: int = 0
    total_workers: int = 0
    active_workers: int = 0

    # 工单统计
    total_work_orders: int = 0
    pending_orders: int = 0
    in_progress_orders: int = 0
    completed_orders: int = 0

    # 今日统计
    today_plan_qty: int = 0
    today_completed_qty: int = 0
    today_completion_rate: float = 0.0
    today_actual_hours: float = 0.0

    # 质量统计
    today_qualified_qty: int = 0
    today_pass_rate: float = 0.0

    # 异常统计
    open_exceptions: int = 0
    critical_exceptions: int = 0

    # 设备统计
    total_equipment: int = 0
    running_equipment: int = 0
    maintenance_equipment: int = 0
    fault_equipment: int = 0

    # 车间统计
    workshop_stats: List[Dict[str, Any]] = []


class WorkshopTaskBoardResponse(BaseModel):
    """车间任务看板响应"""
    workshop_id: int
    workshop_name: str
    workstations: List[Dict[str, Any]] = []
    work_orders: List[Dict[str, Any]] = []
    workers: List[Dict[str, Any]] = []


class ProductionEfficiencyReportResponse(BaseModel):
    """生产效率报表响应"""
    report_date: date
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_hours: float = 0.0
    actual_hours: float = 0.0
    efficiency: float = 0.0
    plan_qty: int = 0
    completed_qty: int = 0
    completion_rate: float = 0.0
    qualified_qty: int = 0
    pass_rate: float = 0.0


class CapacityUtilizationResponse(BaseModel):
    """产能利用率响应"""
    workshop_id: int
    workshop_name: str
    date: date
    capacity_hours: Optional[float] = None
    actual_hours: float = 0.0
    utilization_rate: float = 0.0
    plan_hours: float = 0.0
    load_rate: float = 0.0


class WorkerPerformanceReportResponse(BaseModel):
    """人员绩效报表响应"""
    worker_id: int
    worker_code: str
    worker_name: str
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    period_start: date
    period_end: date
    total_hours: float = 0.0
    total_reports: int = 0
    completed_orders: int = 0
    total_completed_qty: int = 0
    total_qualified_qty: int = 0
    average_efficiency: float = 0.0


class WorkerRankingResponse(BaseModel):
    """人员绩效排名响应"""
    rank: int
    worker_id: int
    worker_name: str
    workshop_name: Optional[str] = None
    efficiency: float = 0.0
    output: int = 0
    quality_rate: float = 0.0
    total_hours: float = 0.0
    score: float = 0.0

