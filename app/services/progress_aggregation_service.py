# -*- coding: utf-8 -*-
"""Re-export wrapper — canonical implementation lives in progress_service.py."""

from app.services.progress_service import (  # noqa: F401
    aggregate_task_progress,
    ProgressAggregationService,
)

__all__ = ["aggregate_task_progress", "ProgressAggregationService"]
