# -*- coding: utf-8 -*-
"""
Schedule Generation 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for schedule_generation
    from .schedulegeneration import router
except ImportError:
    try:
        from .schedule import router
    except ImportError:
        try:
            from .common.schedule_generation import router
        except ImportError:
            try:
                from .admin.schedule_generation import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'schedule_generation module placeholder'}

__all__ = ['router']
