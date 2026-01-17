# -*- coding: utf-8 -*-
"""
回款管理 API endpoints 聚合

包含：
- 收款计划调整
- 收款计划调整历史
- 回款记录列表
- 回款登记
- 回款统计分析
- 回款提醒
- 回款详情
- 发票核销
- 收款计划列表
- 回款记录导出
- 应收账款导出
"""

from fastapi import APIRouter

from .payment_exports import router as payment_exports_router
from .payment_plans import router as payment_plans_router
from .payment_records import router as payment_records_router
from .payment_statistics import router as payment_statistics_router

router = APIRouter()

# 注册子路由
router.include_router(payment_plans_router)
router.include_router(payment_records_router)
router.include_router(payment_statistics_router)
router.include_router(payment_exports_router)
