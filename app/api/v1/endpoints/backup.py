# -*- coding: utf-8 -*-
"""
Backup 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for backup
    from .backup import router
except ImportError:
    try:
        from .backup import router
    except ImportError:
        try:
            from .common.backup import router
        except ImportError:
            try:
                from .admin.backup import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'backup module placeholder'}

__all__ = ['router']
