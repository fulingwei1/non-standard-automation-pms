# -*- coding: utf-8 -*-
"""
工时提醒相关 Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import PaginatedResponse, TimestampSchema


# ==================== 提醒规则配置 ====================


class ReminderConfigCreate(BaseModel):
    """创建提醒规则配置"""
    rule_code: str = Field(..., description="规则编码")
    rule_name: str = Field(..., description="规则名称")
    reminder_type: str = Field(..., description="提醒类型")
    rule_parameters: Dict[str, Any] = Field(..., description="规则参数")
    apply_to_departments: Optional[List[int]] = Field(None, description="适用部门ID列表")
    apply_to_roles: Optional[List[int]] = Field(None, description="适用角色ID列表")
    apply_to_users: Optional[List[int]] = Field(None, description="适用用户ID列表")
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道列表")
    notification_template: Optional[str] = Field(None, description="通知模板")
    remind_frequency: str = Field(default='ONCE_DAILY', description="提醒频率")
    max_reminders_per_day: int = Field(default=1, description="每日最大提醒次数")
    priority: str = Field(default='NORMAL', description="优先级")


class ReminderConfigUpdate(BaseModel):
    """更新提醒规则配置"""
    rule_name: Optional[str] = None
    rule_parameters: Optional[Dict[str, Any]] = None
    apply_to_departments: Optional[List[int]] = None
    apply_to_roles: Optional[List[int]] = None
    apply_to_users: Optional[List[int]] = None
    notification_channels: Optional[List[str]] = None
    notification_template: Optional[str] = None
    remind_frequency: Optional[str] = None
    max_reminders_per_day: Optional[int] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None


class ReminderConfigResponse(TimestampSchema):
    """提醒规则配置响应"""
    id: int
    rule_code: str
    rule_name: str
    reminder_type: str
    rule_parameters: Dict[str, Any]
    apply_to_departments: Optional[List[int]] = None
    apply_to_roles: Optional[List[int]] = None
    apply_to_users: Optional[List[int]] = None
    notification_channels: Optional[List[str]] = None
    notification_template: Optional[str] = None
    remind_frequency: str
    max_reminders_per_day: int
    priority: str
    is_active: bool
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ReminderConfigListResponse(PaginatedResponse):
    """提醒规则配置列表响应"""
    items: List[ReminderConfigResponse]


# ==================== 提醒记录 ====================


class ReminderRecordResponse(TimestampSchema):
    """提醒记录响应"""
    id: int
    reminder_no: str
    reminder_type: str
    config_id: Optional[int] = None
    user_id: int
    user_name: Optional[str] = None
    title: str
    content: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None
    status: str
    notification_channels: Optional[List[str]] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    dismissed_by: Optional[int] = None
    dismissed_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    priority: str

    class Config:
        from_attributes = True


class ReminderRecordListResponse(PaginatedResponse):
    """提醒记录列表响应"""
    items: List[ReminderRecordResponse]


class ReminderDismissRequest(BaseModel):
    """忽略提醒请求"""
    reason: Optional[str] = Field(None, description="忽略原因")


# ==================== 异常记录 ====================


class AnomalyRecordResponse(TimestampSchema):
    """异常记录响应"""
    id: int
    timesheet_id: int
    user_id: int
    user_name: Optional[str] = None
    anomaly_type: str
    description: str
    anomaly_data: Optional[Dict[str, Any]] = None
    severity: str
    detected_at: datetime
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_note: Optional[str] = None
    reminder_id: Optional[int] = None

    class Config:
        from_attributes = True


class AnomalyRecordListResponse(PaginatedResponse):
    """异常记录列表响应"""
    items: List[AnomalyRecordResponse]


class AnomalyResolveRequest(BaseModel):
    """解决异常请求"""
    resolution_note: Optional[str] = Field(None, description="解决说明")


# ==================== 统计信息 ====================


class ReminderStatistics(BaseModel):
    """提醒统计信息"""
    total_reminders: int = Field(description="总提醒数")
    pending_reminders: int = Field(description="待处理提醒数")
    sent_reminders: int = Field(description="已发送提醒数")
    dismissed_reminders: int = Field(description="已忽略提醒数")
    resolved_reminders: int = Field(description="已解决提醒数")
    by_type: Dict[str, int] = Field(description="按类型统计")
    by_priority: Dict[str, int] = Field(description="按优先级统计")
    recent_reminders: List[ReminderRecordResponse] = Field(description="最近提醒")


class AnomalyStatistics(BaseModel):
    """异常统计信息"""
    total_anomalies: int = Field(description="总异常数")
    unresolved_anomalies: int = Field(description="未解决异常数")
    resolved_anomalies: int = Field(description="已解决异常数")
    by_type: Dict[str, int] = Field(description="按类型统计")
    by_severity: Dict[str, int] = Field(description="按严重程度统计")
    recent_anomalies: List[AnomalyRecordResponse] = Field(description="最近异常")


# ==================== Dashboard ====================


class ReminderDashboard(BaseModel):
    """提醒Dashboard"""
    reminder_stats: ReminderStatistics = Field(description="提醒统计")
    anomaly_stats: AnomalyStatistics = Field(description="异常统计")
    active_configs: List[ReminderConfigResponse] = Field(description="活跃规则配置")
    urgent_items: List[ReminderRecordResponse] = Field(description="紧急事项")
