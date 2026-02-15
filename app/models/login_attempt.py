# -*- coding: utf-8 -*-
"""
登录尝试记录模型
用于审计和安全分析
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.models.base import Base


class LoginAttempt(Base):
    """登录尝试记录"""
    
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    username = Column(String(50), nullable=False, index=True, comment="用户名")
    ip_address = Column(String(45), nullable=False, index=True, comment="IP地址（支持IPv6）")
    user_agent = Column(Text, comment="用户代理（浏览器信息）")
    success = Column(Boolean, default=False, nullable=False, index=True, comment="是否成功")
    failure_reason = Column(String(50), comment="失败原因：wrong_password, user_not_found, account_locked等")
    locked = Column(Boolean, default=False, nullable=False, comment="此次尝试后是否导致账户锁定")
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True, comment="尝试时间")
    
    def __repr__(self):
        return f"<LoginAttempt(username={self.username}, ip={self.ip_address}, success={self.success})>"
