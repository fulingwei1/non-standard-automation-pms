# -*- coding: utf-8 -*-
"""
工作日志模块 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime

from .common import TimestampSchema, PaginatedResponse


# ==================== 工作日志 ====================

class WorkLogCreate(BaseModel):
    """创建工作日志"""
    work_date: date = Field(description="工作日期")
    content: str = Field(description="工作内容（限制300字）")
    mentioned_projects: Optional[List[int]] = Field(default=[], description="提及的项目ID列表")
    mentioned_machines: Optional[List[int]] = Field(default=[], description="提及的设备ID列表")
    mentioned_users: Optional[List[int]] = Field(default=[], description="提及的人员ID列表")
    status: Optional[str] = Field(default="SUBMITTED", description="状态：DRAFT/SUBMITTED")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v):
        if len(v) > 300:
            raise ValueError('工作内容不能超过300字')
        if len(v.strip()) == 0:
            raise ValueError('工作内容不能为空')
        return v


class WorkLogUpdate(BaseModel):
    """更新工作日志"""
    content: Optional[str] = Field(default=None, description="工作内容（限制300字）")
    mentioned_projects: Optional[List[int]] = Field(default=None, description="提及的项目ID列表")
    mentioned_machines: Optional[List[int]] = Field(default=None, description="提及的设备ID列表")
    mentioned_users: Optional[List[int]] = Field(default=None, description="提及的人员ID列表")
    status: Optional[str] = Field(default=None, description="状态：DRAFT/SUBMITTED")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v):
        if v is not None and len(v) > 300:
            raise ValueError('工作内容不能超过300字')
        if v is not None and len(v.strip()) == 0:
            raise ValueError('工作内容不能为空')
        return v


class MentionResponse(BaseModel):
    """提及响应"""
    id: int
    mention_type: str
    mention_id: int
    mention_name: Optional[str] = None


class WorkLogResponse(TimestampSchema):
    """工作日志响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    work_date: date
    content: str
    status: str
    mentions: List[MentionResponse] = []


class WorkLogListResponse(PaginatedResponse):
    """工作日志列表响应"""
    items: List[WorkLogResponse]


# ==================== 工作日志配置 ====================

class WorkLogConfigCreate(BaseModel):
    """创建工作日志配置"""
    user_id: Optional[int] = Field(default=None, description="用户ID（NULL表示全员）")
    department_id: Optional[int] = Field(default=None, description="部门ID（可选）")
    is_required: bool = Field(default=True, description="是否必须提交")
    is_active: bool = Field(default=True, description="是否启用")
    remind_time: str = Field(default="18:00", description="提醒时间（HH:mm格式）")


class WorkLogConfigUpdate(BaseModel):
    """更新工作日志配置"""
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    remind_time: Optional[str] = None


class WorkLogConfigResponse(TimestampSchema):
    """工作日志配置响应"""
    id: int
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    is_required: bool
    is_active: bool
    remind_time: str


class WorkLogConfigListResponse(BaseModel):
    """工作日志配置列表响应"""
    items: List[WorkLogConfigResponse]


# ==================== 提及选项 ====================

class MentionOption(BaseModel):
    """提及选项"""
    id: int
    name: str
    type: str  # PROJECT/MACHINE/USER


class MentionOptionsResponse(BaseModel):
    """提及选项响应"""
    projects: List[MentionOption] = []
    machines: List[MentionOption] = []
    users: List[MentionOption] = []
