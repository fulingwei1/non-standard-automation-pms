# -*- coding: utf-8 -*-
"""
Tenants 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Tenants is typically in access control or multi-tenant related areas
    from .access_control.tenants import router
except ImportError:
    try:
        from .auth.tenants import router
    except ImportError:
        try:
            from .multi_tenancy.tenants import router
        except ImportError:
            try:
                from .settings.tenants import router
            except ImportError:
                from fastapi import APIRouter

                router = APIRouter()

__all__ = ['router']
