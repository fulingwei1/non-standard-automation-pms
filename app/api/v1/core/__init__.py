# -*- coding: utf-8 -*-
"""
API核心工具模块
提供通用的API工具和基类
"""

from app.api.v1.core.project_crud_base import ProjectCRUDRouter, create_project_crud_router

__all__ = [
    "create_project_crud_router",
    "ProjectCRUDRouter",
]
