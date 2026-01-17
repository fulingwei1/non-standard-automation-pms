# -*- coding: utf-8 -*-
"""
客服服务 API - 模块化结构
"""

from fastapi import APIRouter

from .communications import router as communications_router
from .knowledge import router as knowledge_router
from .knowledge_features import router as knowledge_features_router
from .records import router as records_router
from .statistics import router as statistics_router
from .survey_templates import router as survey_templates_router
from .surveys import router as surveys_router
from .tickets import router as tickets_router

router = APIRouter()

router.include_router(tickets_router, prefix="/tickets")
router.include_router(records_router, prefix="/records")
router.include_router(communications_router, prefix="/communications")
router.include_router(surveys_router, prefix="/surveys")
router.include_router(survey_templates_router, prefix="/survey-templates")
router.include_router(knowledge_router, prefix="/knowledge-base")
router.include_router(knowledge_features_router, prefix="/knowledge-features")
router.include_router(statistics_router, prefix="/statistics")

__all__ = ["router"]
