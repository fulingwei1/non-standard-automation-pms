# -*- coding: utf-8 -*-
"""
生产进度跟踪系统 - Pydantic Schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 进度日志 Schemas ====================

class ProductionProgressLogBase(BaseModel):
    """进度日志基础Schema"""
    work_order_id: int
    workstation_id: Optional[int] = None
    current_progress: int = Field(..., ge=0, le=100, description="当前进度(%)")
    completed_qty: int = Field(default=0, ge=0, description="已完成数量")
    qualified_qty: int = Field(default=0, ge=0, description="合格数量")
    defect_qty: int = Field(default=0, ge=0, description="不良数量")
    work_hours: Optional[Decimal] = Field(None, ge=0, description="本次工时")
    status: str = Field(..., description="工单状态")
    note: Optional[str] = None


class ProductionProgressLogCreate(ProductionProgressLogBase):
    """创建进度日志"""
    pass


class ProductionProgressLogResponse(ProductionProgressLogBase):
    """进度日志响应"""
    id: int
    previous_progress: int
    progress_delta: Optional[int]
    cumulative_hours: Optional[Decimal]
    previous_status: Optional[str]
    logged_at: datetime
    logged_by: int
    plan_progress: Optional[int]
    deviation: Optional[int]
    is_delayed: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 工位状态 Schemas ====================

class WorkstationStatusBase(BaseModel):
    """工位状态基础Schema"""
    workstation_id: int
    current_state: str = Field(..., description="当前状态：IDLE/BUSY/PAUSED/MAINTENANCE/OFFLINE")
    current_work_order_id: Optional[int] = None
    current_operator_id: Optional[int] = None


class WorkstationStatusUpdate(BaseModel):
    """更新工位状态"""
    current_state: Optional[str] = None
    current_work_order_id: Optional[int] = None
    current_operator_id: Optional[int] = None
    current_progress: Optional[int] = Field(None, ge=0, le=100)
    completed_qty_today: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


class WorkstationStatusResponse(WorkstationStatusBase):
    """工位状态响应"""
    id: int
    current_progress: int
    completed_qty_today: int
    target_qty_today: int
    capacity_utilization: Decimal
    work_hours_today: Decimal
    idle_hours_today: Decimal
    planned_hours_today: Decimal
    efficiency_rate: Optional[Decimal]
    quality_rate: Decimal
    is_bottleneck: int
    bottleneck_level: int
    alert_count: int
    status_updated_at: datetime
    last_work_start_time: Optional[datetime]
    last_work_end_time: Optional[datetime]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 进度预警 Schemas ====================

class ProgressAlertBase(BaseModel):
    """进度预警基础Schema"""
    work_order_id: int
    workstation_id: Optional[int] = None
    alert_type: str = Field(..., description="预警类型：DELAY/BOTTLENECK/QUALITY/EFFICIENCY/CAPACITY")
    alert_level: str = Field(default="WARNING", description="预警级别：INFO/WARNING/CRITICAL/URGENT")
    alert_title: str
    alert_message: str


class ProgressAlertCreate(ProgressAlertBase):
    """创建进度预警"""
    current_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    deviation_value: Optional[Decimal] = None
    rule_code: Optional[str] = None
    rule_name: Optional[str] = None


class ProgressAlertDismiss(BaseModel):
    """关闭预警"""
    resolution_note: Optional[str] = None


class ProgressAlertResponse(ProgressAlertBase):
    """进度预警响应"""
    id: int
    current_value: Optional[Decimal]
    threshold_value: Optional[Decimal]
    deviation_value: Optional[Decimal]
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[int]
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    dismissed_at: Optional[datetime]
    dismissed_by: Optional[int]
    action_taken: Optional[str]
    resolution_note: Optional[str]
    rule_code: Optional[str]
    rule_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 业务 Schemas ====================

class RealtimeProgressOverview(BaseModel):
    """实时进度总览"""
    total_work_orders: int
    in_progress: int
    completed_today: int
    delayed: int
    active_workstations: int
    idle_workstations: int
    bottleneck_workstations: int
    active_alerts: int
    critical_alerts: int
    overall_progress: Decimal = Field(description="整体进度(%)")
    overall_capacity_utilization: Decimal = Field(description="整体产能利用率(%)")
    efficiency_rate: Decimal = Field(description="平均效率(%)")


class WorkOrderProgressTimeline(BaseModel):
    """工单进度时间线"""
    work_order_id: int
    work_order_no: str
    task_name: str
    current_progress: int
    current_status: str
    plan_start_date: Optional[datetime]
    plan_end_date: Optional[datetime]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    timeline: List[ProductionProgressLogResponse]
    alerts: List[ProgressAlertResponse]


class BottleneckWorkstation(BaseModel):
    """瓶颈工位"""
    workstation_id: int
    workstation_code: str
    workstation_name: str
    workshop_name: str
    bottleneck_level: int
    capacity_utilization: Decimal
    work_hours_today: Decimal
    idle_hours_today: Decimal
    current_work_order_count: int
    pending_work_order_count: int
    alert_count: int
    bottleneck_reason: str


class ProgressDeviation(BaseModel):
    """进度偏差分析"""
    work_order_id: int
    work_order_no: str
    task_name: str
    plan_progress: int
    actual_progress: int
    deviation: int
    deviation_percentage: Decimal
    is_delayed: bool
    plan_end_date: Optional[datetime]
    estimated_completion_date: Optional[datetime]
    delay_days: Optional[int]
    risk_level: str


class ProgressStatistics(BaseModel):
    """进度统计"""
    date: datetime
    total_work_orders: int
    on_schedule: int
    delayed: int
    ahead_of_schedule: int
    average_progress: Decimal
    average_deviation: Decimal
    completion_rate: Decimal


# ==================== API 请求参数 ====================

class RealtimeProgressQuery(BaseModel):
    """实时进度查询参数"""
    workshop_id: Optional[int] = None
    workstation_id: Optional[int] = None
    status: Optional[str] = None


class BottleneckQuery(BaseModel):
    """瓶颈查询参数"""
    workshop_id: Optional[int] = None
    min_level: int = Field(default=1, ge=1, le=3, description="最小瓶颈等级")
    limit: int = Field(default=10, ge=1, le=100)


class AlertQuery(BaseModel):
    """预警查询参数"""
    work_order_id: Optional[int] = None
    workstation_id: Optional[int] = None
    alert_type: Optional[str] = None
    alert_level: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class DeviationQuery(BaseModel):
    """偏差查询参数"""
    workshop_id: Optional[int] = None
    min_deviation: int = Field(default=10, description="最小偏差(%)")
    only_delayed: bool = Field(default=True, description="只显示延期")
