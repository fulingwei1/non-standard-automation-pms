# -*- coding: utf-8 -*-
"""
售后服务 API - 模块化结构
"""

from fastapi import APIRouter

from .statistics import router as statistics_router
from .tickets import router as tickets_router
from .records import router as records_router
from .communications import router as communications_router
from .surveys import router as surveys_router
from .survey_templates import router as survey_templates_router
from .knowledge import router as knowledge_router
from .knowledge_features import router as knowledge_features_router

router = APIRouter()

router.include_router(statistics_router)
router.include_router(tickets_router)
router.include_router(records_router)
router.include_router(communications_router)
router.include_router(surveys_router)
router.include_router(survey_templates_router)
router.include_router(knowledge_router)
router.include_router(knowledge_features_router)

__all__ = ['router']
