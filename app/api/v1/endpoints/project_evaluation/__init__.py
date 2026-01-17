# -*- coding: utf-8 -*-
"""
项目评价模块

拆分自原 project_evaluation.py (560行)，按功能域分为：
- statistics: 评价统计
- evaluations: 项目评价 CRUD
- dimensions: 评价维度配置

IMPORTANT: 路由顺序很重要！
静态路由（如 /evaluations/statistics, /dimensions/weights/summary）必须在
参数化路由（如 /evaluations/{eval_id}, /dimensions/{dim_id}）之前定义。
"""

from fastapi import APIRouter

from .dimensions import router as dimensions_router
from .evaluations import router as evaluations_router
from .statistics import router as statistics_router

router = APIRouter()

# 统计路由（/evaluations/statistics 必须在 evaluations 之前，避免与 /{eval_id} 冲突）
router.include_router(statistics_router, tags=["评价统计"])

# 项目评价 CRUD（包含 /evaluations 和 /evaluations/{eval_id}）
router.include_router(evaluations_router, tags=["项目评价"])

# 维度配置（内部已处理 /dimensions/weights/summary 在 /{dim_id} 之前）
router.include_router(dimensions_router, tags=["评价维度"])
