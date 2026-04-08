# -*- coding: utf-8 -*-
"""
Gantt Dependency 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for gantt_dependency
    from .ganttdependency import router
except ImportError:
    try:
        from .gantt import router
    except ImportError:
        try:
            from .common.gantt_dependency import router
        except ImportError:
            try:
                from .admin.gantt_dependency import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'gantt_dependency module placeholder'}

__all__ = ['router']
