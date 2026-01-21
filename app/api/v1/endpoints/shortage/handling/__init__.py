"""
缺料管理 - Handling 层（缺料处理）

职责：解决问题
- 缺料上报（reports）
- 物料替代（substitutions）
- 物料调拨（transfers）
- 到货跟踪（arrivals）
"""
from fastapi import APIRouter

from . import reports, substitutions, transfers, arrivals

router = APIRouter()

router.include_router(reports.router, prefix="/reports", tags=["缺料-问题处理"])
router.include_router(substitutions.router, prefix="/substitutions", tags=["缺料-问题处理"])
router.include_router(transfers.router, prefix="/transfers", tags=["缺料-问题处理"])
router.include_router(arrivals.router, prefix="/arrivals", tags=["缺料-问题处理"])
