# -*- coding: utf-8 -*-
"""
租户模型 (Tenant Model)

多租户 SaaS 架构的核心模型，用于隔离不同租户的数据。
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "ACTIVE"           # 正常
    SUSPENDED = "SUSPENDED"     # 暂停
    DELETED = "DELETED"         # 已删除


class TenantPlan(str, Enum):
    """租户套餐"""
    FREE = "FREE"               # 免费版
    STANDARD = "STANDARD"       # 标准版
    ENTERPRISE = "ENTERPRISE"   # 企业版


class Tenant(Base, TimestampMixin):
    """租户表"""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_code = Column(String(50), unique=True, nullable=False, comment="租户编码（唯一标识）")
    tenant_name = Column(String(200), nullable=False, comment="租户名称")
    status = Column(String(20), default=TenantStatus.ACTIVE.value, comment="状态")
    plan_type = Column(String(20), default=TenantPlan.FREE.value, comment="套餐类型")

    # 限制配置
    max_users = Column(Integer, default=5, comment="最大用户数")
    max_roles = Column(Integer, default=5, comment="最大角色数")
    max_storage_gb = Column(Integer, default=1, comment="最大存储空间(GB)")

    # 租户配置（JSON）
    settings = Column(JSON, comment="租户配置")

    # 联系信息
    contact_name = Column(String(100), comment="联系人姓名")
    contact_email = Column(String(200), comment="联系邮箱")
    contact_phone = Column(String(50), comment="联系电话")

    # 有效期
    expired_at = Column(DateTime, comment="过期时间")

    # 关系
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    roles = relationship("Role", back_populates="tenant", lazy="dynamic")

    def __repr__(self):
        return f"<Tenant {self.tenant_code}>"

    @property
    def is_active(self) -> bool:
        """是否处于活跃状态"""
        return self.status == TenantStatus.ACTIVE.value

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expired_at is None:
            return False
        return datetime.utcnow() > self.expired_at

    def get_plan_limits(self) -> dict:
        """获取套餐限制"""
        plan_limits = {
            TenantPlan.FREE.value: {"users": 5, "roles": 5, "storage_gb": 1},
            TenantPlan.STANDARD.value: {"users": 50, "roles": 20, "storage_gb": 10},
            TenantPlan.ENTERPRISE.value: {"users": -1, "roles": -1, "storage_gb": 100},  # -1 表示无限
        }
        return plan_limits.get(self.plan_type, plan_limits[TenantPlan.FREE.value])
