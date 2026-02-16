# -*- coding: utf-8 -*-
"""
缺料管理 API - 三层架构

按业务流程重构为三层：
1. Detection（预警检测）- 发现问题
2. Handling（问题处理）- 解决问题
3. Analytics（统计报表）- 分析问题

菜单映射：
- 缺料预警: /shortage/detection/...
- 缺料管理: /shortage/handling/...
- 缺料分析: /shortage/analytics/...
"""

from fastapi import APIRouter

from .detection import router as detection_router
from .handling import router as handling_router
from .analytics import router as analytics_router
from .smart_alerts import router as smart_alerts_router

router = APIRouter()

# Smart Alerts 层 - 智能预警系统 (Team 3)
# 路由: /alerts, /scan, /forecast, /analysis
router.include_router(smart_alerts_router, prefix="/smart", tags=["智能缺料预警"])

# Detection 层 - 预警检测
# 路由: /alerts, /inventory-warnings
router.include_router(detection_router, prefix="/detection", tags=["缺料-预警检测"])

# Handling 层 - 问题处理
# 路由: /reports, /substitutions, /transfers, /arrivals
router.include_router(handling_router, prefix="/handling", tags=["缺料-问题处理"])

# Analytics 层 - 统计报表
# 路由: /statistics/..., /dashboard, /daily-report, /trends
router.include_router(analytics_router, prefix="/analytics", tags=["缺料-统计报表"])

__all__ = ['router']
