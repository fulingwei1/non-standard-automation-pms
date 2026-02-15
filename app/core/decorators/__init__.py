# -*- coding: utf-8 -*-
"""
装饰器模块

提供各种 API 装饰器功能。
"""

from .tenant_isolation import (
    allow_cross_tenant,
    require_tenant_isolation,
    tenant_resource_check,
)

__all__ = [
    'require_tenant_isolation',
    'allow_cross_tenant',
    'tenant_resource_check',
]
