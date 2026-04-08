# -*- coding: utf-8 -*-
"""
Quote Actual Compare 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for quote_actual_compare
    from .quoteactualcompare import router
except ImportError:
    try:
        from .quote import router
    except ImportError:
        try:
            from .common.quote_actual_compare import router
        except ImportError:
            try:
                from .admin.quote_actual_compare import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'quote_actual_compare module placeholder'}

__all__ = ['router']
