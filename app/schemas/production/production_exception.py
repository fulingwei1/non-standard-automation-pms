# -*- coding: utf-8 -*-
"""
production_exception Schemas

包含production_exception相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import PaginatedResponse, TimestampSchema


# ==================== 生产异常 ====================

class ProductionExceptionCreate(BaseModel):
    """创建生产异常"""
    exception_type: str = Field(description="异常类型：MATERIAL/EQUIPMENT/QUALITY/OTHER")
    exception_level: str = Field(default="MINOR", description="异常级别：MINOR/MAJOR/CRITICAL")
    title: str = Field(max_length=200, description="异常标题")
    description: Optional[str] = Field(default=None, description="异常描述")
    work_order_id: Optional[int] = Field(default=None, description="关联工单ID")
    project_id: Optional[int] = Field(default=None, description="关联项目ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    equipment_id: Optional[int] = Field(default=None, description="设备ID")
    impact_hours: Optional[Decimal] = Field(default=None, description="影响工时(小时)")
    impact_cost: Optional[Decimal] = Field(default=None, description="影响成本(元)")
    remark: Optional[str] = None


class ProductionExceptionHandle(BaseModel):
    """处理生产异常"""
    handle_plan: str = Field(description="处理方案")
    handle_result: Optional[str] = Field(default=None, description="处理结果")


class ProductionExceptionResponse(TimestampSchema):
    """生产异常响应"""
    id: int
    exception_no: str
    exception_type: str
    exception_level: str
    title: str
    description: Optional[str] = None
    work_order_id: Optional[int] = None
    work_order_no: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    reporter_id: int
    reporter_name: Optional[str] = None
    report_time: datetime
    status: str
    handler_id: Optional[int] = None
    handler_name: Optional[str] = None
    handle_plan: Optional[str] = None
    handle_result: Optional[str] = None
    handle_time: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    impact_hours: Optional[Decimal] = None
    impact_cost: Optional[Decimal] = None
    remark: Optional[str] = None


class ProductionExceptionListResponse(PaginatedResponse):
    """生产异常列表响应"""
    items: List[ProductionExceptionResponse]


