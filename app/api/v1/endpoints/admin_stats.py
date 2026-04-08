# -*- coding: utf-8 -*-
"""
Admin Stats 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for admin_stats
    from .adminstats import router
except ImportError:
    try:
        from .admin import router
    except ImportError:
            try:
                from .admin import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                router.get('/')(
                    lambda: {'message': 'admin_stats module placeholder'}
                )

__all__ = ['router']
