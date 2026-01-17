# -*- coding: utf-8 -*-
"""
模板管理 API 路由聚合

包含报价模板、合同模板和CPQ规则集的所有端点
"""

from fastapi import APIRouter

from .contract_templates import router as contract_templates_router
from .cpq_rules import router as cpq_rules_router
from .quote_templates import router as quote_templates_router

router = APIRouter()

# 包含所有子路由
router.include_router(quote_templates_router)
router.include_router(contract_templates_router)
router.include_router(cpq_rules_router)

__all__ = ["router"]
