# -*- coding: utf-8 -*-
"""
Project Workspace 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Re-export the real project workspace router for the legacy
    # /project-workspace prefix used by the frontend.
    from .projects.workspace import router
except ImportError:
    try:
        from .projectworkspace import router
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
