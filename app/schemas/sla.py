# -*- coding: utf-8 -*-
"""
SLA管理模块 Schemas
包含：SLA策略、SLA监控记录
"""

from typing import Optional, List, Any, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


# ==================== SLA策略 ====================

class SLAPolicyCreate(BaseModel):
    """创建SLA策略"""
    policy_name: str = Field(..., description="策略名称")
    policy_code: str = Field(..., description="策略编码")
    problem_type: Optional[str] = Field(None, description="问题类型（可选，为空表示适用所有类型）")
    urgency: Optional[str] = Field(None, description="紧急程度（可选，为空表示适用所有紧急程度）")
    response_time_hours: int = Field(..., gt=0, description="响应时间（小时）")
    resolve_time_hours: int = Field(..., gt=0, description="解决时间（小时）")
    warning_threshold_percent: Optional[Decimal] = Field(80, ge=0, le=100, description="预警阈值（百分比）")
    priority: Optional[int] = Field(100, description="优先级（数字越小优先级越高）")
    description: Optional[str] = Field(None, description="策略描述")
    remark: Optional[str] = Field(None, description="备注")


class SLAPolicyUpdate(BaseModel):
    """更新SLA策略"""
    policy_name: Optional[str] = Field(None, description="策略名称")
    problem_type: Optional[str] = Field(None, description="问题类型")
    urgency: Optional[str] = Field(None, description="紧急程度")
    response_time_hours: Optional[int] = Field(None, gt=0, description="响应时间（小时）")
    resolve_time_hours: Optional[int] = Field(None, gt=0, description="解决时间（小时）")
    warning_threshold_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="预警阈值（百分比）")
    priority: Optional[int] = Field(None, description="优先级")
    is_active: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="策略描述")
    remark: Optional[str] = Field(None, description="备注")


class SLAPolicyResponse(BaseModel):
    """SLA策略响应"""
    id: int
    policy_name: str
    policy_code: str
    problem_type: Optional[str] = None
    urgency: Optional[str] = None
    response_time_hours: int
    resolve_time_hours: int
    warning_threshold_percent: Optional[Decimal] = None
    priority: int
    is_active: bool
    description: Optional[str] = None
    remark: Optional[str] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== SLA监控记录 ====================

class SLAMonitorResponse(BaseModel):
    """SLA监控记录响应"""
    id: int
    ticket_id: int
    ticket_no: Optional[str] = None
    policy_id: int
    policy_name: Optional[str] = None
    policy_code: Optional[str] = None
    response_deadline: datetime
    resolve_deadline: datetime
    actual_response_time: Optional[datetime] = None
    actual_resolve_time: Optional[datetime] = None
    response_status: str
    resolve_status: str
    response_time_diff_hours: Optional[Decimal] = None
    resolve_time_diff_hours: Optional[Decimal] = None
    response_warning_sent: bool
    resolve_warning_sent: bool
    response_warning_sent_at: Optional[datetime] = None
    resolve_warning_sent_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== SLA统计 ====================

class SLAStatisticsResponse(BaseModel):
    """SLA统计响应"""
    total_tickets: int = Field(..., description="总工单数")
    monitored_tickets: int = Field(..., description="已监控工单数")
    response_on_time: int = Field(..., description="响应按时数")
    response_overdue: int = Field(..., description="响应超时数")
    response_warning: int = Field(..., description="响应预警数")
    resolve_on_time: int = Field(..., description="解决按时数")
    resolve_overdue: int = Field(..., description="解决超时数")
    resolve_warning: int = Field(..., description="解决预警数")
    response_rate: Decimal = Field(..., description="响应按时率（%）")
    resolve_rate: Decimal = Field(..., description="解决按时率（%）")
    avg_response_time_hours: Optional[Decimal] = Field(None, description="平均响应时间（小时）")
    avg_resolve_time_hours: Optional[Decimal] = Field(None, description="平均解决时间（小时）")
    by_policy: Optional[List[Dict[str, Any]]] = Field(None, description="按策略统计")
    by_problem_type: Optional[List[Dict[str, Any]]] = Field(None, description="按问题类型统计")
    by_urgency: Optional[List[Dict[str, Any]]] = Field(None, description="按紧急程度统计")
