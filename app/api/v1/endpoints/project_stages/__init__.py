# -*- coding: utf-8 -*-
"""
项目阶段实例 API 模块

提供项目阶段/节点的初始化、状态流转、进度查询等接口

模块结构:
 ├── initialization.py  # 阶段初始化
 ├── progress.py        # 进度查询
 ├── stage_operations.py  # 阶段操作
 ├── node_operations.py   # 节点操作
 ├── custom_nodes.py     # 自定义节点
 ├── node_assignment.py  # 节点分配
 ├── views.py           # 视图API
 └── status_updates.py   # 状态更新
"""

from fastapi import APIRouter

from . import (
    custom_nodes,
    initialization,
    node_assignment,
    node_operations,
    progress,
    stage_operations,
    status_updates,
    views,
)

# 创建主路由
router = APIRouter()

# 聚合所有子路由
router.include_router(initialization.router, tags=["project-stages"])
router.include_router(progress.router, tags=["project-stages"])
router.include_router(stage_operations.router, tags=["project-stages"])
router.include_router(node_operations.router, tags=["project-stages"])
router.include_router(custom_nodes.router, tags=["project-stages"])
router.include_router(node_assignment.router, tags=["project-stages"])
router.include_router(views.router, tags=["project-stages"])
router.include_router(status_updates.router, tags=["project-stages"])

__all__ = ["router"]
