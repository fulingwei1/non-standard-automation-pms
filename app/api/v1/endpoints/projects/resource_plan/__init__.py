# -*- coding: utf-8 -*-
"""
项目资源计划路由聚合

提供项目阶段资源计���的管理功能:
- CRUD: 资源计划的增删改查
- assignment: 人员分配与释放
"""

from fastapi import APIRouter

from . import assignment, crud

router = APIRouter()

# CRUD 操作
router.include_router(crud.router)

# 分配操作
router.include_router(assignment.router)
