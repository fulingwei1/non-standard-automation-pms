# -*- coding: utf-8 -*-
"""
Change Impact 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for change_impact
    from .changeimpact import router
except ImportError:
    try:
        from .change import router
    except ImportError:
        try:
            from .common.change_impact import router
        except ImportError:
            try:
                from .admin.change_impact import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'change_impact module placeholder'}

__all__ = ['router']
