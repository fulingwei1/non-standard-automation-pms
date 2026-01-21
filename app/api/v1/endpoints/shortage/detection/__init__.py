"""
缺料管理 - Detection 层（预警检测）

职责：发现问题
- 预警管理（alerts）
- 齐套检查、库存监控（monitoring）
"""
from fastapi import APIRouter

from . import alerts, monitoring

router = APIRouter()

router.include_router(alerts.router, tags=["缺料-预警检测"])
router.include_router(monitoring.router, tags=["缺料-预警检测"])
