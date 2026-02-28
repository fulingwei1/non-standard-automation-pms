# -*- coding: utf-8 -*-
"""
项目模板端点 - 路由聚合

已拆分为模块化结构：
- template_crud.py: 模板基础CRUD操作
- template_projects.py: 从模板创建项目
- template_versions.py: 版本管理（CRUD、发布、比较、回滚）
- template_analytics.py: 推荐模板和使用统计
"""

from fastapi import APIRouter

from . import template_analytics, template_crud, template_projects, template_versions

router = APIRouter()

# 聚合所有子路由（静态路径在前，动态路径/{id}在后）
router.include_router(template_analytics.router)  # /templates/recommend 等静态路径
router.include_router(template_projects.router)   # /templates/{id}/create-project
router.include_router(template_crud.router)       # /templates/{id} CRUD
router.include_router(template_versions.router)   # 版本管理
