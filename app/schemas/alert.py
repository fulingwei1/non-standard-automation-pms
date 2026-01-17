# -*- coding: utf-8 -*-
"""
预警与异常管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema, TimestampSchema

# ==================== 预警规则 ====================

class AlertRuleCreate(BaseModel):
    """创建预警规则"""
    rule_code: str = Field(max_length=50)
    rule_name: str = Field(max_length=200)
    rule_type: str = Field(description="规则类型")
    target_type: str = Field(description="监控对象类型")
    target_field: Optional[str] = None
    condition_type: str = Field(description="条件类型")
    condition_operator: Optional[str] = None
    threshold_value: Optional[str] = None
    threshold_min: Optional[str] = None
    threshold_max: Optional[str] = None
    condition_expr: Optional[str] = None
    alert_level: str = Field(default="WARNING")
    advance_days: int = Field(default=0, ge=0)
    notify_channels: Optional[List[str]] = None
    notify_roles: Optional[List[str]] = None
    notify_users: Optional[List[int]] = None
    check_frequency: str = Field(default="DAILY")
    description: Optional[str] = None
    solution_guide: Optional[str] = None


class AlertRuleUpdate(BaseModel):
    """更新预警规则"""
    rule_name: Optional[str] = None
    target_field: Optional[str] = None
    condition_operator: Optional[str] = None
    threshold_value: Optional[str] = None
    threshold_min: Optional[str] = None
    threshold_max: Optional[str] = None
    condition_expr: Optional[str] = None
    alert_level: Optional[str] = None
    advance_days: Optional[int] = None
    notify_channels: Optional[List[str]] = None
    notify_roles: Optional[List[str]] = None
    notify_users: Optional[List[int]] = None
    check_frequency: Optional[str] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None
    solution_guide: Optional[str] = None


class AlertRuleResponse(TimestampSchema):
    """预警规则响应"""
    id: int
    rule_code: str
    rule_name: str
    rule_type: str
    target_type: str
    condition_type: str
    alert_level: str
    advance_days: int = 0
    check_frequency: str = "DAILY"
    is_enabled: bool = True
    is_system: bool = False


# ==================== 预警记录 ====================

class AlertRecordHandle(BaseModel):
    """处理预警"""
    handle_result: str
    handle_note: Optional[str] = None


class AlertRecordResponse(TimestampSchema):
    """预警记录响应"""
    id: int
    alert_no: str
    rule_id: int
    rule_name: Optional[str] = None
    target_type: str
    target_id: int
    target_no: Optional[str] = None
    target_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    alert_level: str
    alert_title: str
    alert_content: str
    triggered_at: Optional[datetime] = None
    trigger_value: Optional[str] = None
    threshold_value: Optional[str] = None
    status: str = "PENDING"
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    handler_id: Optional[int] = None
    handler_name: Optional[str] = None
    handle_start_at: Optional[datetime] = None
    handle_end_at: Optional[datetime] = None
    handle_result: Optional[str] = None


class AlertRecordListResponse(BaseSchema):
    """预警记录列表响应"""
    id: int
    alert_no: str
    alert_level: str
    alert_title: str
    target_type: str
    target_name: Optional[str] = None
    project_name: Optional[str] = None
    triggered_at: datetime
    status: str
    handler_name: Optional[str] = None


# ==================== 异常事件 ====================

class ExceptionEventCreate(BaseModel):
    """创建异常事件"""
    source_type: str = Field(description="来源类型")
    source_id: Optional[int] = None
    alert_id: Optional[int] = None
    project_id: Optional[int] = None
    machine_id: Optional[int] = None
    event_type: str = Field(description="异常类型")
    severity: str = Field(description="严重程度")
    event_title: str = Field(max_length=200)
    event_description: str
    discovery_location: Optional[str] = None
    impact_scope: Optional[str] = None
    impact_description: Optional[str] = None
    schedule_impact: int = Field(default=0)
    cost_impact: Optional[Decimal] = Field(default=0)
    responsible_dept: Optional[str] = None
    responsible_user_id: Optional[int] = None
    due_date: Optional[date] = None
    attachments: Optional[List[Any]] = None


class ExceptionEventUpdate(BaseModel):
    """更新异常事件"""
    severity: Optional[str] = None
    event_title: Optional[str] = None
    event_description: Optional[str] = None
    impact_scope: Optional[str] = None
    impact_description: Optional[str] = None
    schedule_impact: Optional[int] = None
    cost_impact: Optional[Decimal] = None
    responsible_dept: Optional[str] = None
    responsible_user_id: Optional[int] = None
    due_date: Optional[date] = None
    root_cause: Optional[str] = None
    cause_category: Optional[str] = None
    solution: Optional[str] = None
    preventive_measures: Optional[str] = None
    status: Optional[str] = None


class ExceptionEventResolve(BaseModel):
    """解决异常"""
    solution: str
    preventive_measures: Optional[str] = None
    resolution_note: Optional[str] = None


class ExceptionEventVerify(BaseModel):
    """验证异常"""
    verification_result: str = Field(description="VERIFIED/REJECTED")
    note: Optional[str] = None


class ExceptionEventResponse(TimestampSchema):
    """异常事件响应"""
    id: int
    event_no: str
    source_type: str
    alert_id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    event_type: str
    severity: str
    event_title: str
    event_description: str
    discovered_at: Optional[datetime] = None
    discovered_by: Optional[int] = None
    discovered_by_name: Optional[str] = None
    impact_scope: Optional[str] = None
    schedule_impact: int = 0
    cost_impact: Decimal = 0
    status: str = "OPEN"
    responsible_dept: Optional[str] = None
    responsible_user_id: Optional[int] = None
    responsible_user_name: Optional[str] = None
    due_date: Optional[date] = None
    is_overdue: bool = False
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ExceptionEventListResponse(BaseSchema):
    """异常事件列表响应"""
    id: int
    event_no: str
    event_type: str
    severity: str
    event_title: str
    project_name: Optional[str] = None
    status: str
    responsible_user_name: Optional[str] = None
    due_date: Optional[date] = None
    is_overdue: bool = False
    discovered_at: datetime


# ==================== 项目健康度 ====================

class ProjectHealthResponse(BaseSchema):
    """项目健康度响应"""
    project_id: int
    project_name: str
    snapshot_date: date
    overall_health: str
    schedule_health: Optional[str] = None
    cost_health: Optional[str] = None
    quality_health: Optional[str] = None
    health_score: int = 0
    open_alerts: int = 0
    open_exceptions: int = 0
    blocking_issues: int = 0
    schedule_variance: Decimal = 0
    cost_variance: Decimal = 0


# ==================== 统计 ====================

class AlertStatisticsResponse(BaseSchema):
    """预警统计响应"""
    stat_date: date
    stat_type: str
    total_alerts: int = 0
    info_alerts: int = 0
    warning_alerts: int = 0
    critical_alerts: int = 0
    urgent_alerts: int = 0
    pending_alerts: int = 0
    resolved_alerts: int = 0
    total_exceptions: int = 0
    open_exceptions: int = 0
    avg_response_time: Decimal = 0
    avg_resolve_time: Decimal = 0


# ==================== 预警订阅 ====================

class AlertSubscriptionCreate(BaseModel):
    """创建预警订阅"""
    alert_type: Optional[str] = Field(None, description="预警类型（空表示全部）")
    project_id: Optional[int] = Field(None, description="项目ID（空表示全部）")
    min_level: str = Field(default="WARNING", description="最低接收级别")
    notify_channels: Optional[List[str]] = Field(default=["SYSTEM"], description="通知渠道")
    quiet_start: Optional[str] = Field(None, description="免打扰开始时间（HH:mm格式）")
    quiet_end: Optional[str] = Field(None, description="免打扰结束时间（HH:mm格式）")
    is_active: bool = Field(default=True, description="是否启用")


class AlertSubscriptionUpdate(BaseModel):
    """更新预警订阅"""
    alert_type: Optional[str] = None
    project_id: Optional[int] = None
    min_level: Optional[str] = None
    notify_channels: Optional[List[str]] = None
    quiet_start: Optional[str] = None
    quiet_end: Optional[str] = None
    is_active: Optional[bool] = None


class AlertSubscriptionResponse(TimestampSchema):
    """预警订阅响应"""
    id: int
    user_id: int
    alert_type: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    min_level: str = "WARNING"
    notify_channels: Optional[List[str]] = None
    quiet_start: Optional[str] = None
    quiet_end: Optional[str] = None
    is_active: bool = True
