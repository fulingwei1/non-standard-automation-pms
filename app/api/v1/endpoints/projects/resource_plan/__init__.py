# -*- coding: utf-8 -*-
"""
项目资源计划路由聚合

提供项目阶段资源计���的管理功能:
- CRUD: 资源计划的增删改查
- assignment: 人员分配与释放
"""

from fastapi import APIRouter

from . import assignment, crud, custom

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /summary）必须在动态路径（如 /{plan_id}）之前注册

# 先注册自定义端点（静态路径）
router.include_router(custom.router)

# 再注册CRUD路由（动态路径）
router.include_router(crud.router)

# 分配操作
router.include_router(assignment.router)
