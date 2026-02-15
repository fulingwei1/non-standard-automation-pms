# -*- coding: utf-8 -*-
"""
数据库核心模块

提供租户感知的数据库查询功能。
"""

from .tenant_query import TenantQuery, create_tenant_aware_session

__all__ = [
    'TenantQuery',
    'create_tenant_aware_session',
]
