# -*- coding: utf-8 -*-
"""
资源排程与负荷管理模块

拆分自原 workload.py (895行)，按功能域分为：
- utils: 辅助工具函数
- user_workload: 用户负荷查询
- team_workload: 团队负荷概览和看板
- visualization: 热力图、甘特图、可用资源
- skills: 技能管理和匹配
"""

from fastapi import APIRouter

from .skills import router as skills_router
from .team_workload import router as team_router
from .user_workload import router as user_router
from .visualization import router as viz_router

router = APIRouter()

# 用户负荷
router.include_router(user_router, tags=["用户负荷"])

# 团队负荷
router.include_router(team_router, tags=["团队负荷"])

# 可视化
router.include_router(viz_router, tags=["负荷可视化"])

# 技能管理
router.include_router(skills_router, tags=["技能管理"])
