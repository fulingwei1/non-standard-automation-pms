# -*- coding: utf-8 -*-
"""
Cost Collection 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for cost_collection
    from .costcollection import router
except ImportError:
    try:
        from .cost import router
    except ImportError:
        try:
            from .common.cost_collection import router
        except ImportError:
            try:
                from .admin.cost_collection import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'cost_collection module placeholder'}

__all__ = ['router']
