# -*- coding: utf-8 -*-
"""
安装调试派工模块 Schemas
包含：安装调试派工单
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse

# ==================== 安装调试派工单 ====================

class InstallationDispatchOrderCreate(BaseModel):
    """创建安装调试派工单"""
    project_id: int = Field(..., description="项目ID")
    machine_id: Optional[int] = Field(None, description="机台ID")
    customer_id: int = Field(..., description="客户ID")
    task_type: str = Field(..., description="任务类型")
    task_title: str = Field(..., description="任务标题")
    task_description: Optional[str] = Field(None, description="任务描述")
    location: Optional[str] = Field(None, description="现场地点")
    scheduled_date: date = Field(..., description="计划日期")
    estimated_hours: Optional[Decimal] = Field(None, description="预计工时（小时）")
    priority: str = Field(default='NORMAL', description="优先级")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_phone: Optional[str] = Field(None, description="客户电话")
    customer_address: Optional[str] = Field(None, description="客户地址")
    remark: Optional[str] = Field(None, description="备注")


class InstallationDispatchOrderUpdate(BaseModel):
    """更新安装调试派工单"""
    task_title: Optional[str] = Field(None, description="任务标题")
    task_description: Optional[str] = Field(None, description="任务描述")
    location: Optional[str] = Field(None, description="现场地点")
    scheduled_date: Optional[date] = Field(None, description="计划日期")
    estimated_hours: Optional[Decimal] = Field(None, description="预计工时（小时）")
    priority: Optional[str] = Field(None, description="优先级")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_phone: Optional[str] = Field(None, description="客户电话")
    customer_address: Optional[str] = Field(None, description="客户地址")
    remark: Optional[str] = Field(None, description="备注")


class InstallationDispatchOrderAssign(BaseModel):
    """派工安装调试派工单"""
    assigned_to_id: int = Field(..., description="派工人员ID")
    remark: Optional[str] = Field(None, description="派工备注")


class InstallationDispatchOrderStart(BaseModel):
    """开始安装调试任务"""
    start_time: Optional[datetime] = Field(None, description="开始时间（默认当前时间）")


class InstallationDispatchOrderComplete(BaseModel):
    """完成安装调试任务"""
    end_time: Optional[datetime] = Field(None, description="结束时间（默认当前时间）")
    actual_hours: Optional[Decimal] = Field(None, description="实际工时（小时）")
    execution_notes: Optional[str] = Field(None, description="执行说明")
    issues_found: Optional[str] = Field(None, description="发现的问题")
    solution_provided: Optional[str] = Field(None, description="提供的解决方案")
    photos: Optional[List[str]] = Field(None, description="现场照片列表")


class InstallationDispatchOrderProgress(BaseModel):
    """更新安装调试任务进度"""
    progress: int = Field(..., ge=0, le=100, description="进度百分比（0-100）")
    execution_notes: Optional[str] = Field(None, description="执行说明")


class InstallationDispatchOrderResponse(BaseModel):
    """安装调试派工单响应"""
    id: int
    order_no: str
    project_id: int
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    machine_id: Optional[int] = None
    machine_no: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    task_type: str
    task_title: str
    task_description: Optional[str] = None
    location: Optional[str] = None
    scheduled_date: date
    estimated_hours: Optional[Decimal] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    assigned_by_id: Optional[int] = None
    assigned_by_name: Optional[str] = None
    assigned_time: Optional[datetime] = None
    status: str
    priority: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_hours: Optional[Decimal] = None
    progress: int
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    execution_notes: Optional[str] = None
    issues_found: Optional[str] = None
    solution_provided: Optional[str] = None
    photos: Optional[List[str]] = None
    service_record_id: Optional[int] = None
    acceptance_order_id: Optional[int] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstallationDispatchOrderBatchAssign(BaseModel):
    """批量派工"""
    order_ids: List[int] = Field(..., description="派工单ID列表")
    assigned_to_id: int = Field(..., description="派工人员ID")
    remark: Optional[str] = Field(None, description="派工备注")


class InstallationDispatchStatistics(BaseModel):
    """安装调试派工统计"""
    total: int = Field(..., description="总数")
    pending: int = Field(..., description="待派工")
    assigned: int = Field(..., description="已派工")
    in_progress: int = Field(..., description="进行中")
    completed: int = Field(..., description="已完成")
    cancelled: int = Field(..., description="已取消")
    urgent: int = Field(..., description="紧急")
