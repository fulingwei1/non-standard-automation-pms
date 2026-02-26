# -*- coding: utf-8 -*-
"""Re-export wrapper — canonical implementation lives in progress_service.py."""

from app.services.progress_service import ProgressAutoService  # noqa: F401

__all__ = ["ProgressAutoService"]
