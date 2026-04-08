# -*- coding: utf-8 -*-
"""
Team Generation 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for team_generation
    from .teamgeneration import router
except ImportError:
    try:
        from .team import router
    except ImportError:
        try:
            from .common.team_generation import router
        except ImportError:
            try:
                from .admin.team_generation import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'team_generation module placeholder'}

__all__ = ['router']
