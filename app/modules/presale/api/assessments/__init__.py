# -*- coding: utf-8 -*-
"""
技术评估管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import assessments, failure_cases, open_items, scoring_rules

# 创建主路由
router = APIRouter()

# 注册子模块路由
router.include_router(assessments.router, tags=["sales-assessments"])
router.include_router(failure_cases.router, tags=["sales-failure-cases"])
router.include_router(open_items.router, tags=["sales-open-items"])
router.include_router(scoring_rules.router, tags=["sales-scoring-rules"])
