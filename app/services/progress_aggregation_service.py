# -*- coding: utf-8 -*-
"""
进度聚合服务 - 兼容层

[DEPRECATED] 此模块已废弃，请使用 app.services.progress_service

所有功能已迁移至 progress_service.py，本文件保留用于向后兼容。
"""

import warnings

# 发出废弃警告
warnings.warn(
    "progress_aggregation_service 已废弃，请使用 app.services.progress_service",
    DeprecationWarning,
    stacklevel=2,
)

# 从新模块重新导出所有符号，保持向后兼容
from app.services.progress_service import (
    ProgressAggregationService,
    _check_and_update_health,
    aggregate_task_progress,
    create_progress_log,
    get_project_progress_summary,
)

__all__ = [
    "ProgressAggregationService",
    "_check_and_update_health",
    "aggregate_task_progress",
    "create_progress_log",
    "get_project_progress_summary",
]
