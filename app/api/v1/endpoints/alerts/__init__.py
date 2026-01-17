# -*- coding: utf-8 -*-
"""
预警与异常管理 API
拆分后的模块化结构

包含：
- rules.py: 预警规则管理
- records.py: 预警记录管理
- notifications.py: 预警通知管理
- exceptions.py: 异常事件管理
- statistics.py: 统计分析
- subscriptions.py: 订阅管理
- exports.py: 导出功能
"""

from fastapi import APIRouter

from .exceptions import router as exceptions_router
from .exports import router as exports_router
from .notifications import router as notifications_router
from .records import router as records_router

# 导入子路由
from .rules import router as rules_router
from .statistics import router as statistics_router
from .subscriptions import router as subscriptions_router

# 创建主路由
router = APIRouter()

# 包含所有子路由（保持原有的URL路径）
# 重要：statistics_router 必须在 records_router 之前注册
# 因为 records_router 有 /alerts/{alert_id} 路由会匹配 /alerts/statistics
router.include_router(rules_router)
router.include_router(statistics_router)  # 先注册 /alerts/statistics 等具体路由
router.include_router(records_router)     # 再注册 /alerts/{alert_id} 参数化路由
router.include_router(notifications_router)
router.include_router(exceptions_router)
router.include_router(subscriptions_router)
router.include_router(exports_router)

# 导出
__all__ = ['router']
