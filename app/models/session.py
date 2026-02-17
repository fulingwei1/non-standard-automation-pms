# -*- coding: utf-8 -*-
"""
用户会话模型
用于管理用户的登录会话，支持多设备登录和会话管理
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class UserSession(Base, TimestampMixin):
    """
    用户会话表
    
    用于存储和管理用户的登录会话信息，支持：
    - 多设备登录追踪
    - 会话超时管理
    - 设备指纹绑定
    - 异地登录检测
    - 强制下线功能
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        comment="用户ID"
    )
    
    # Token信息
    access_token_jti = Column(
        String(64), 
        nullable=False, 
        unique=True, 
        index=True,
        comment="Access Token的JTI（JWT ID）"
    )
    refresh_token_jti = Column(
        String(64), 
        nullable=False, 
        unique=True, 
        index=True,
        comment="Refresh Token的JTI"
    )
    
    # 设备信息
    device_id = Column(
        String(128), 
        nullable=True,
        comment="设备唯一标识（客户端生成）"
    )
    device_name = Column(
        String(100), 
        nullable=True,
        comment="设备名称（如：Chrome on Windows）"
    )
    device_type = Column(
        String(50), 
        nullable=True,
        comment="设备类型：desktop/mobile/tablet"
    )
    
    # 网络信息
    ip_address = Column(
        String(50), 
        nullable=True,
        comment="登录IP地址"
    )
    location = Column(
        String(200), 
        nullable=True,
        comment="地理位置（基于IP）"
    )
    
    # User-Agent信息
    user_agent = Column(
        Text, 
        nullable=True,
        comment="浏览器User-Agent"
    )
    browser = Column(
        String(50), 
        nullable=True,
        comment="浏览器名称"
    )
    os = Column(
        String(50), 
        nullable=True,
        comment="操作系统"
    )
    
    # 会话状态
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="会话是否活跃"
    )
    
    # 时间信息
    login_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment="登录时间"
    )
    last_activity_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment="最后活动时间"
    )
    expires_at = Column(
        DateTime, 
        nullable=False,
        comment="会话过期时间"
    )
    logout_at = Column(
        DateTime, 
        nullable=True,
        comment="登出时间"
    )
    
    # 安全标记
    is_suspicious = Column(
        Boolean, 
        default=False,
        comment="是否为可疑登录（异地/异常设备）"
    )
    risk_score = Column(
        Integer, 
        default=0,
        comment="风险评分（0-100）"
    )
    
    # 关系
    user = relationship("User", backref="sessions")
    
    # 索引
    __table_args__ = (
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_ip_address", "ip_address"),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, device={self.device_name}, active={self.is_active})>"
