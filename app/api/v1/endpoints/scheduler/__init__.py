# -*- coding: utf-8 -*-
"""
调度器管理模块

拆分自原 scheduler.py (680行)，按功能域分为：
- status: 调度器状态、任务列表、手动触发、服务列表
- metrics: 运行指标（JSON和Prometheus格式）
- configs: 定时任务配置管理
"""

from fastapi import APIRouter

from .configs import router as configs_router
from .metrics import router as metrics_router
from .status import router as status_router

router = APIRouter()

# 状态和任务管理
router.include_router(status_router, tags=["调度器状态"])

# 指标监控
router.include_router(metrics_router, tags=["调度器指标"])

# 配置管理
router.include_router(configs_router, tags=["调度器配置"])
