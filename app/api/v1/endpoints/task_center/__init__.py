# -*- coding: utf-8 -*-
"""
任务中心 API - 模块化结构
"""

from fastapi import APIRouter

from .batch import router as batch_router
from .comments import router as comments_router
from .complete import router as complete_router
from .create import router as create_router
from .detail import router as detail_router
from .my_tasks import router as my_tasks_router
from .overview import router as overview_router
from .reject import router as reject_router
from .transfer import router as transfer_router
from .update import router as update_router

router = APIRouter()

router.include_router(overview_router)
router.include_router(my_tasks_router)
router.include_router(detail_router)
router.include_router(create_router)
router.include_router(update_router)
router.include_router(complete_router)
router.include_router(transfer_router)
router.include_router(reject_router)
router.include_router(comments_router)
router.include_router(batch_router)

__all__ = ['router']
