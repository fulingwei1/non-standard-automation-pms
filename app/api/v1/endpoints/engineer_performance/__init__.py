# -*- coding: utf-8 -*-
"""
工程师绩效评价 API 端点
"""

from fastapi import APIRouter

from .summary import router as summary_router
from .ranking import router as ranking_router
from .engineer import router as engineer_router
from .collaboration import router as collaboration_router
from .knowledge import router as knowledge_router
from .config import router as config_router

router = APIRouter(prefix="/engineer-performance", tags=["工程师绩效"])

# 注册子路由
router.include_router(summary_router)
router.include_router(ranking_router)
router.include_router(engineer_router)
router.include_router(collaboration_router)
router.include_router(knowledge_router)
router.include_router(config_router)
