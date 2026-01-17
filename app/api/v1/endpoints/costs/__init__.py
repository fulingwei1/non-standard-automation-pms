"""
成本管理 API 路由聚合模块

本模块聚合成本管理的所有子模块路由：
- basic: 成本基础CRUD操作
- analysis: 成本分析和统计
- labor: 人工成本计算
- allocation: 成本分摊
- budget: 预算执行分析
- review: 成本复盘
- alert: 成本预警
"""

from fastapi import APIRouter

from app.api.v1.endpoints.costs import (
    alert,
    allocation,
    analysis,
    basic,
    budget,
    labor,
    review,
)

router = APIRouter()

# 注册子模块路由
router.include_router(basic.router, tags=["成本管理-基础操作"])
router.include_router(analysis.router, tags=["成本管理-分析统计"])
router.include_router(labor.router, prefix="/labor", tags=["成本管理-人工成本"])
router.include_router(allocation.router, prefix="/allocation", tags=["成本管理-成本分摊"])
router.include_router(budget.router, prefix="/budget", tags=["成本管理-预算分析"])
router.include_router(review.router, prefix="/review", tags=["成本管理-成本复盘"])
router.include_router(alert.router, prefix="/alert", tags=["成本管理-成本预警"])

__all__ = ["router"]
