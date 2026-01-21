# -*- coding: utf-8 -*-
"""
work_order Schemas

包含work_order相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema, PaginatedResponse, TimestampSchema


# ==================== 生产工单 ====================

class WorkOrderCreate(BaseModel):
    """创建工单"""
    task_name: str = Field(max_length=200, description="任务名称")
    task_type: str = Field(description="工单类型：MACHINING/ASSEMBLY/DEBUGGING等")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    machine_id: Optional[int] = Field(default=None, description="机台ID")
    production_plan_id: Optional[int] = Field(default=None, description="生产计划ID")
    process_id: Optional[int] = Field(default=None, description="工序ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    workstation_id: Optional[int] = Field(default=None, description="工位ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    material_name: Optional[str] = Field(default=None, description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    drawing_no: Optional[str] = Field(default=None, description="图纸编号")
    plan_qty: int = Field(default=1, description="计划数量")
    standard_hours: Optional[Decimal] = Field(default=None, description="标准工时")
    plan_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    plan_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: str = Field(default="NORMAL", description="优先级")
    work_content: Optional[str] = Field(default=None, description="工作内容")
    remark: Optional[str] = Field(default=None, description="备注")


class WorkOrderUpdate(BaseModel):
    """更新工单"""
    task_name: Optional[str] = None
    plan_qty: Optional[int] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    priority: Optional[str] = None
    work_content: Optional[str] = None
    remark: Optional[str] = None


class WorkOrderAssignRequest(BaseModel):
    """工单派工请求"""
    worker_id: Optional[int] = Field(default=None, description="指派给(工人ID)")
    workstation_id: Optional[int] = Field(default=None, description="工位ID")


class WorkOrderResponse(TimestampSchema):
    """工单响应"""
    id: int
    work_order_no: str
    task_name: str
    task_type: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    production_plan_id: Optional[int] = None
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    workstation_id: Optional[int] = None
    workstation_name: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    plan_qty: int
    completed_qty: int
    qualified_qty: int
    defect_qty: int
    standard_hours: Optional[float] = None
    actual_hours: float
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    assigned_to: Optional[int] = None
    assigned_worker_name: Optional[str] = None
    status: str
    priority: str
    progress: int
    work_content: Optional[str] = None
    remark: Optional[str] = None


class WorkOrderListResponse(PaginatedResponse):
    """工单列表响应"""
    items: List[WorkOrderResponse]


class WorkReportItem(BaseModel):
    """报工记录项"""
    id: int
    report_no: str
    report_type: str
    report_time: datetime
    progress_percent: Optional[int] = None
    work_hours: Optional[float] = None
    completed_qty: Optional[int] = None
    qualified_qty: Optional[int] = None


class WorkOrderProgressResponse(BaseModel):
    """工单进度响应"""
    work_order_id: int
    work_order_no: str
    progress: int
    plan_qty: int
    completed_qty: int
    qualified_qty: int
    defect_qty: int
    standard_hours: Optional[float] = None
    actual_hours: float
    reports: Optional[List[WorkReportItem]] = Field(default=[], description="报工记录列表")


