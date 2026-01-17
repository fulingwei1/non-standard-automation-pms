# -*- coding: utf-8 -*-
"""
齐套率与物料保障模块

拆分自原 kit_rate.py (669行)，按功能域分为：
- utils: 齐套率计算工具函数
- machine: 机台级齐套率、物料状态
- project: 项目级齐套率、物料汇总、缺料清单
- dashboard: 齐套看板、趋势分析
"""

from fastapi import APIRouter

from .dashboard import router as dashboard_router
from .machine import router as machine_router
from .project import router as project_router

router = APIRouter()

# 机台级齐套率
router.include_router(machine_router, tags=["机台齐套率"])

# 项目级齐套率
router.include_router(project_router, tags=["项目齐套率"])

# 看板和趋势
router.include_router(dashboard_router, tags=["齐套看板"])
