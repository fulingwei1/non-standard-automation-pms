# -*- coding: utf-8 -*-
"""
PMO API - 模块化结构
"""

from fastapi import APIRouter

from .closure import router as closure_router
from .cockpit import router as cockpit_router
from .initiation import router as initiation_router
from .meetings import router as meetings_router
from .phases import router as phases_router
from .risks import router as risks_router

router = APIRouter()

router.include_router(initiation_router)
router.include_router(phases_router)
router.include_router(risks_router)
router.include_router(closure_router)
router.include_router(cockpit_router)
router.include_router(meetings_router)

__all__ = ['router']
