# -*- coding: utf-8 -*-
"""
任务进度更新服务 - 兼容层

[DEPRECATED] 此模块已废弃，请使用 app.services.progress_service

所有功能已迁移至 progress_service.py，本文件保留用于向后兼容。
"""

import warnings

# 发出废弃警告
warnings.warn(
    "task_progress_service 已废弃，请使用 app.services.progress_service",
    DeprecationWarning,
    stacklevel=2,
)

# 从新模块重新导出所有符号，保持向后兼容
from app.services.progress_service import (
    apply_task_progress_update,
    progress_error_to_http,
    update_task_progress,
)

__all__ = [
    "apply_task_progress_update",
    "progress_error_to_http",
    "update_task_progress",
]
