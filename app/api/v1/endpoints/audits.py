# -*- coding: utf-8 -*-
"""
Audits 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for audits
    from .audits import router
except ImportError:
    try:
        from .audits import router
    except ImportError:
        try:
            from .common.audits import router
        except ImportError:
            try:
                from .admin.audits import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'audits module placeholder'}

__all__ = ['router']
