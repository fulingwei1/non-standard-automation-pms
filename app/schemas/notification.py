# -*- coding: utf-8 -*-
"""
通知中心 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseSchema, TimestampSchema, PaginatedResponse


class NotificationResponse(TimestampSchema):
    """通知响应"""
    id: int
    user_id: int
    notification_type: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    link_url: Optional[str] = None
    link_params: Optional[Dict[str, Any]] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    priority: str = "NORMAL"
    extra_data: Optional[Dict[str, Any]] = None


class NotificationListResponse(PaginatedResponse):
    """通知列表响应"""
    items: List[NotificationResponse]


class NotificationSettingsResponse(TimestampSchema):
    """通知设置响应"""
    id: int
    user_id: int
    email_enabled: bool = True
    sms_enabled: bool = False
    wechat_enabled: bool = True
    system_enabled: bool = True
    task_notifications: bool = True
    approval_notifications: bool = True
    alert_notifications: bool = True
    issue_notifications: bool = True
    project_notifications: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationSettingsUpdate(BaseModel):
    """更新通知设置"""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    wechat_enabled: Optional[bool] = None
    system_enabled: Optional[bool] = None
    task_notifications: Optional[bool] = None
    approval_notifications: Optional[bool] = None
    alert_notifications: Optional[bool] = None
    issue_notifications: Optional[bool] = None
    project_notifications: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class BatchReadRequest(BaseModel):
    """批量标记已读请求"""
    notification_ids: List[int] = Field(description="通知ID列表")



