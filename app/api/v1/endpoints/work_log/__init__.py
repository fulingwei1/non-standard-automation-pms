# -*- coding: utf-8 -*-
"""
工作日志模块

拆分自原 work_log.py (563行)，按功能域分为：
- crud: 工作日志创建、列表、提及选项
- config: 工作日志配置管理
- ai: AI智能分析和项目推荐
- detail: 工作日志详情、更新、删除

IMPORTANT: 路由顺序很重要！
静态路由（如 /work-logs/config, /work-logs/suggested-projects）必须在
参数化路由（如 /work-logs/{work_log_id}）之前定义，否则 FastAPI 会将
"config" 或 "suggested-projects" 误解析为 work_log_id 参数。
"""

from fastapi import APIRouter

from .ai import router as ai_router
from .config import router as config_router
from .crud import router as crud_router
from .detail import router as detail_router

router = APIRouter()

# 工作日志基础操作（包含 /work-logs 和 /work-logs/mentions/options）
router.include_router(crud_router, tags=["工作日志"])

# 工作日志配置（/work-logs/config 系列，必须在 detail 之前）
router.include_router(config_router, tags=["日志配置"])

# AI分析（/work-logs/ai-analyze 和 /work-logs/suggested-projects，必须在 detail 之前）
router.include_router(ai_router, tags=["AI分析"])

# 工作日志详情操作（/work-logs/{work_log_id} 系列，必须在最后）
router.include_router(detail_router, tags=["日志详情"])
