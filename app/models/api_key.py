# -*- coding: utf-8 -*-
"""
API Key数据模型
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class APIKey(Base):
    """API Key模型"""
    
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="API Key名称/描述")
    key_hash = Column(String(64), unique=True, nullable=False, index=True, comment="API Key哈希值（SHA256）")
    key_prefix = Column(String(20), nullable=True, comment="API Key前缀（用于识别）")
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户")
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, comment="所属租户")
    
    # 权限和范围
    scopes = Column(JSON, nullable=True, comment="权限范围列表")
    
    # 安全限制
    allowed_ips = Column(JSON, nullable=True, comment="IP白名单")
    rate_limit = Column(Integer, nullable=True, comment="速率限制（请求/分钟）")
    
    # 状态和使用
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 元数据
    metadata = Column(JSON, nullable=True, comment="额外元数据")
    notes = Column(Text, nullable=True, comment="备注说明")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="api_keys")
    tenant = relationship("Tenant", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>"
