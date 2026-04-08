# -*- coding: utf-8 -*-
"""
Stage Templates 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for stage_templates
    from .stagetemplates import router
except ImportError:
    try:
        from .stage import router
    except ImportError:
        try:
            from .common.stage_templates import router
        except ImportError:
            try:
                from .admin.stage_templates import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'stage_templates module placeholder'}

__all__ = ['router']
