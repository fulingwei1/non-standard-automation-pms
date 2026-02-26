# -*- coding: utf-8 -*-
"""Re-export wrapper — canonical implementation lives in progress_service.py."""

from app.services.progress_service import (  # noqa: F401
    apply_task_progress_update,
    update_task_progress,
)

__all__ = ["apply_task_progress_update", "update_task_progress"]
