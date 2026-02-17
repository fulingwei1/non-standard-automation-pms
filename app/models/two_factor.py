# -*- coding: utf-8 -*-
"""
双因素认证（2FA）数据模型
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User2FASecret(Base, TimestampMixin):
    """用户2FA密钥表
    
    存储加密的TOTP密钥，支持多种2FA方式扩展
    """
    
    __tablename__ = "user_2fa_secrets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    secret_encrypted = Column(Text, nullable=False, comment="加密的TOTP密钥")
    method = Column(String(20), default="totp", nullable=False, comment="2FA方式: totp")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 关系
    user = relationship("User", back_populates="two_factor_secrets")
    
    __table_args__ = (
        Index("idx_2fa_user_active", "user_id", "is_active"),
    )
    
    def __repr__(self):
        return f"<User2FASecret user_id={self.user_id} method={self.method}>"


class User2FABackupCode(Base):
    """用户2FA备用码表
    
    每个用户生成10个备用恢复码，仅可使用一次
    """
    
    __tablename__ = "user_2fa_backup_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    code_hash = Column(String(255), nullable=False, comment="备用码哈希值")
    used = Column(Boolean, default=False, comment="是否已使用")
    used_at = Column(DateTime, comment="使用时间")
    used_ip = Column(String(50), comment="使用IP")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="two_factor_backup_codes")
    
    __table_args__ = (
        Index("idx_user_unused", "user_id", "used"),
        Index("idx_code_hash", "code_hash"),
    )
    
    def __repr__(self):
        return f"<User2FABackupCode user_id={self.user_id} used={self.used}>"
