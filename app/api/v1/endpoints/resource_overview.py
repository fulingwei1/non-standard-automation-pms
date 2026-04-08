# -*- coding: utf-8 -*-
"""
Resource Overview 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for resource_overview
    from .resourceoverview import router
except ImportError:
    try:
        from .resource import router
    except ImportError:
        try:
            from .common.resource_overview import router
        except ImportError:
            try:
                from .admin.resource_overview import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'resource_overview module placeholder'}

__all__ = ['router']
