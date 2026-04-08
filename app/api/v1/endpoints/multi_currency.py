# -*- coding: utf-8 -*-
"""
Multi Currency 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for multi_currency
    from .multicurrency import router
except ImportError:
    try:
        from .multi import router
    except ImportError:
        try:
            from .common.multi_currency import router
        except ImportError:
            try:
                from .admin.multi_currency import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'multi_currency module placeholder'}

__all__ = ['router']
