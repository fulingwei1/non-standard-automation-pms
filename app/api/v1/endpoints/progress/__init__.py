# -*- coding: utf-8 -*-
"""
进度跟踪模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import wbs_templates, tasks, reports, summary, batch, statistics, baselines, forecast, auto_processing

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# WBS模板管理路由
router.include_router(wbs_templates.router, tags=["progress-wbs-templates"])

# 任务管理路由
router.include_router(tasks.router, tags=["progress-tasks"])

# 进度报告路由（注意：/progress-reports/statistics 需要在 /progress-reports/{id} 之前）
router.include_router(reports.router, tags=["progress-reports"])

# 进度汇总与可视化路由
router.include_router(summary.router, tags=["progress-summary"])

# 批量操作路由
router.include_router(batch.router, tags=["progress-batch"])

# 统计报表路由
router.include_router(statistics.router, tags=["progress-statistics"])

# 计划基线管理路由
router.include_router(baselines.router, tags=["progress-baselines"])

# 智能化进度预测与依赖巡检路由
router.include_router(forecast.router, tags=["progress-forecast"])

# 自动化处理路由（预测应用、依赖修复等）
router.include_router(auto_processing.router, tags=["progress-auto-processing"])
