# -*- coding: utf-8 -*-
"""
项目模块基础CRUD端点 - 路由聚合

已拆分为模块化结构：
- project_crud.py: 基础CRUD操作（list, get, create, update, delete）
- project_board.py: 看板功能
- project_stats.py: 统计功能
- project_clone.py: 克隆功能
"""

from fastapi import APIRouter

from . import project_board, project_clone, project_crud, project_stats

router = APIRouter()

# 聚合所有子路由
# 注意：路由顺序很重要！静态路径（如/board, /stats）必须在动态路径（如/{project_id}）之前注册
# 否则 /board 会被 /{project_id} 匹配，导致 "board" 被解析为 int 失败
router.include_router(project_board.router)
router.include_router(project_stats.router)
router.include_router(project_clone.router)
router.include_router(project_crud.router)  # 包含 /{project_id} 的路由放最后
