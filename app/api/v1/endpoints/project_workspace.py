# -*- coding: utf-8 -*-
"""
Project Workspace 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for project_workspace
    from .projectworkspace import router
except ImportError:
    try:
        from .project import router
    except ImportError:
        try:
            from .common.project_workspace import router
        except ImportError:
            try:
                from .admin.project_workspace import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'project_workspace module placeholder'}

__all__ = ['router']
