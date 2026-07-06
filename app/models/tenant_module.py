# -*- coding: utf-8 -*-
"""租户模块开通表（tenant_modules）。

记录每个租户开通了哪些业务模块。模块 key 的权威清单在
app/modules/registry.py；闸门语义（缺行时的默认行为由
settings.MODULE_GATING_MODE 决定）见 app/services/tenant_module_service.py。
"""

from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.models.base import Base, TimestampMixin


class TenantModuleStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    TRIAL = "TRIAL"  # 试用：行为同 ENABLED，但受 expires_at 约束


class TenantModule(Base, TimestampMixin):
    __tablename__ = "tenant_modules"
    __table_args__ = (UniqueConstraint("tenant_id", "module_key", name="uq_tenant_module"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, comment="租户ID")
    module_key = Column(String(50), nullable=False, index=True, comment="模块key（见 modules/registry.py）")
    status = Column(String(20), nullable=False, default=TenantModuleStatus.ENABLED.value, comment="开通状态")
    expires_at = Column(DateTime, comment="到期时间（TRIAL/订阅到期）")
    enabled_by = Column(Integer, ForeignKey("users.id"), comment="操作人")
    config = Column(JSON, comment="模块级租户配置")

    def __repr__(self) -> str:
        return f"<TenantModule t={self.tenant_id} {self.module_key}={self.status}>"
