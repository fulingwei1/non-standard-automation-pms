# -*- coding: utf-8 -*-
"""
会话管理相关 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema


class SessionResponse(TimestampSchema):
    """会话响应"""
    id: int
    user_id: int
    
    # Token信息
    access_token_jti: str
    refresh_token_jti: str
    
    # 设备信息
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    
    # 网络信息
    ip_address: Optional[str] = None
    location: Optional[str] = None
    
    # User-Agent信息
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    
    # 会话状态
    is_active: bool
    
    # 时间信息
    login_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    logout_at: Optional[datetime] = None
    
    # 安全标记
    is_suspicious: bool
    risk_score: int
    
    # 是否为当前会话
    is_current: Optional[bool] = None


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse] = Field(default_factory=list, description="会话列表")
    total: int = Field(description="总数")
    active_count: int = Field(description="活跃会话数")


class DeviceInfo(BaseModel):
    """设备信息请求"""
    device_id: Optional[str] = Field(default=None, description="设备唯一标识")
    device_name: Optional[str] = Field(default=None, description="设备名称")
    device_type: Optional[str] = Field(default="desktop", description="设备类型：desktop/mobile/tablet")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(description="刷新令牌")
    device_info: Optional[DeviceInfo] = None


class RefreshTokenResponse(BaseModel):
    """刷新Token响应"""
    access_token: str = Field(description="新的访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")


class LogoutRequest(BaseModel):
    """登出请求"""
    logout_all: bool = Field(default=False, description="是否登出所有设备")


class RevokeSessionRequest(BaseModel):
    """撤销会话请求"""
    session_id: int = Field(description="要撤销的会话ID")
