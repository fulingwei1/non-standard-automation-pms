# -*- coding: utf-8 -*-
"""
合同管理 API 路由聚合
"""

from fastapi import APIRouter

from .approval import router as approval_router
from .basic import router as basic_router
from .deliverables import router as deliverables_router
from .enhanced import router as enhanced_router
from .export import router as export_router
from .payment_plans import router as payment_plans_router
from .sign_project import router as sign_project_router

router = APIRouter()

# 聚合所有子模块路由
router.include_router(enhanced_router, prefix="/enhanced", tags=["合同增强"])
router.include_router(basic_router)
router.include_router(sign_project_router)
router.include_router(deliverables_router)
router.include_router(payment_plans_router)
router.include_router(approval_router)
router.include_router(export_router)
