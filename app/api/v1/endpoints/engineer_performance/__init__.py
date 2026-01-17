# -*- coding: utf-8 -*-
"""
工程师绩效评价 API 端点
"""

from fastapi import APIRouter

from .collaboration import router as collaboration_router
from .config import router as config_router
from .data_collection import router as data_collection_router
from .data_integrity import router as data_integrity_router
from .data_sync import router as data_sync_router
from .engineer import router as engineer_router
from .feedback import router as feedback_router
from .knowledge import router as knowledge_router
from .manager_evaluation import router as manager_evaluation_router
from .ranking import router as ranking_router
from .solution import router as solution_router
from .summary import router as summary_router
from .trend import router as trend_router

router = APIRouter(prefix="/engineer-performance", tags=["工程师绩效"])

# 注册子路由
router.include_router(summary_router)
router.include_router(ranking_router)
router.include_router(engineer_router)
router.include_router(collaboration_router)
router.include_router(knowledge_router)
router.include_router(config_router)
router.include_router(data_collection_router)
router.include_router(manager_evaluation_router)
router.include_router(data_integrity_router)
router.include_router(feedback_router)
router.include_router(trend_router)
router.include_router(solution_router)
router.include_router(data_sync_router)
