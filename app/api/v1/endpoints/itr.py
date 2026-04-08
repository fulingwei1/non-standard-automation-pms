# -*- coding: utf-8 -*-
"""
Itr 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for itr
    from .itr import router
except ImportError:
    try:
        from .itr import router
    except ImportError:
        try:
            from .common.itr import router
        except ImportError:
            try:
                from .admin.itr import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'itr module placeholder'}

__all__ = ['router']
