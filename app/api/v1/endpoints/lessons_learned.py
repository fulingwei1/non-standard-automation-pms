# -*- coding: utf-8 -*-
"""
Lessons Learned 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for lessons_learned
    from .lessonslearned import router
except ImportError:
    try:
        from .lessons import router
    except ImportError:
        try:
            from .common.lessons_learned import router
        except ImportError:
            try:
                from .admin.lessons_learned import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'lessons_learned module placeholder'}

__all__ = ['router']
