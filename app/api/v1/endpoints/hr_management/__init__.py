# -*- coding: utf-8 -*-
"""
人事管理模块

拆分自原 hr_management.py (763行)，按功能域分为：
- transactions: 人事事务（入职/离职/转正/调岗/晋升/调薪）
- contracts: 合同管理
- reminders: 合同到期提醒
- dashboard: 人事仪表板统计
"""

from fastapi import APIRouter

from .contracts import router as contracts_router
from .dashboard import router as dashboard_router
from .reminders import router as reminders_router
from .transactions import router as transactions_router

router = APIRouter()

# 人事事务
router.include_router(transactions_router, tags=["人事事务"])

# 合同管理
router.include_router(contracts_router, tags=["合同管理"])

# 合同提醒
router.include_router(reminders_router, tags=["合同提醒"])

# 仪表板
router.include_router(dashboard_router, tags=["人事仪表板"])
