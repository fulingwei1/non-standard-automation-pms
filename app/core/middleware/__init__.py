# -*- coding: utf-8 -*-
"""
中间件模块
"""

from .auth_middleware import GlobalAuthMiddleware
from .tenant_middleware import (
    TenantContextMiddleware,
    TenantAwareQuery,
    get_current_tenant_id,
    set_current_tenant_id,
    require_same_tenant,
)

__all__ = [
    "GlobalAuthMiddleware",
    "TenantContextMiddleware",
    "TenantAwareQuery",
    "get_current_tenant_id",
    "set_current_tenant_id",
    "require_same_tenant",
]
