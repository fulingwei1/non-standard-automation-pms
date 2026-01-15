# -*- coding: utf-8 -*-
"""
绩效管理 API - 模块化结构
"""

from fastapi import APIRouter

from .individual import router as individual_router
from .team import router as team_router
from .project import router as project_router
from .employee_api import router as employee_api_router
from .manager_api import router as manager_api_router
from .hr_api import router as hr_api_router
from .integration import router as integration_router

router = APIRouter()

router.include_router(individual_router)
router.include_router(team_router)
router.include_router(project_router)
router.include_router(employee_api_router)
router.include_router(manager_api_router)
router.include_router(hr_api_router)
router.include_router(integration_router)

__all__ = ['router']
