# -*- coding: utf-8 -*-
"""
production_plan Schemas

包含production_plan相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema, PaginatedResponse, TimestampSchema


# ==================== 生产计划 ====================

class ProductionPlanCreate(BaseModel):
    """创建生产计划"""
    plan_name: str = Field(max_length=200, description="计划名称")
    plan_type: str = Field(description="计划类型：MASTER/WORKSHOP")
    project_id: Optional[int] = Field(default=None, description="关联项目ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    plan_start_date: date = Field(description="计划开始日期")
    plan_end_date: date = Field(description="计划结束日期")
    description: Optional[str] = Field(default=None, description="计划说明")
    remark: Optional[str] = Field(default=None, description="备注")


class ProductionPlanUpdate(BaseModel):
    """更新生产计划"""
    plan_name: Optional[str] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    description: Optional[str] = None
    remark: Optional[str] = None


class ProductionPlanResponse(TimestampSchema):
    """生产计划响应"""
    id: int
    plan_no: str
    plan_name: str
    plan_type: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_start_date: date
    plan_end_date: date
    status: str
    progress: int
    description: Optional[str] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    remark: Optional[str] = None


class ProductionPlanListResponse(PaginatedResponse):
    """生产计划列表响应"""
    items: List[ProductionPlanResponse]


