# -*- coding: utf-8 -*-
"""
Field Commissioning 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for field_commissioning
    from .fieldcommissioning import router
except ImportError:
    try:
        from .field import router
    except ImportError:
        try:
            from .common.field_commissioning import router
        except ImportError:
            try:
                from .admin.field_commissioning import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'field_commissioning module placeholder'}

__all__ = ['router']
