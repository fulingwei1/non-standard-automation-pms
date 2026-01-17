# -*- coding: utf-8 -*-
"""
文化墙模块

拆分自原 culture_wall.py (463行)，按功能域分为：
- summary: 文化墙汇总（用于滚动播放）
- contents: 文化墙内容管理
- goals: 个人目标管理
"""

from fastapi import APIRouter

from .contents import router as contents_router
from .goals import router as goals_router
from .summary import router as summary_router

router = APIRouter()

# 文化墙汇总（需放在contents之前，避免路由冲突）
router.include_router(summary_router, tags=["文化墙汇总"])

# 文化墙内容管理
router.include_router(contents_router, tags=["文化墙内容"])

# 个人目标管理
router.include_router(goals_router, tags=["个人目标"])
