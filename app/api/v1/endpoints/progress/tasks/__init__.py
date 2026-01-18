# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务管理路由聚合
将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import assignment, crud, dependencies, logs, progress, status, wbs_init

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# WBS初始化路由
router.include_router(wbs_init.router, tags=["progress-tasks"])

# 任务CRUD路由
router.include_router(crud.router, tags=["progress-tasks"])

# 任务状态管理路由
router.include_router(status.router, tags=["progress-tasks"])

# 任务进度更新路由
router.include_router(progress.router, tags=["progress-tasks"])

# 任务依赖管理路由
router.include_router(dependencies.router, tags=["progress-tasks"])

# 任务分配路由
router.include_router(assignment.router, tags=["progress-tasks"])

# 任务进度日志路由
router.include_router(logs.router, tags=["progress-tasks"])
