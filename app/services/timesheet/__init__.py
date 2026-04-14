# -*- coding: utf-8 -*-
"""工时服务兼容入口。"""

from __future__ import annotations

from typing import Any, Dict, Optional


class TimesheetService:
    """轻量兼容服务，保留旧测试所需的基础接口。"""

    def __init__(self, db):
        self.db = db

    async def create_timesheet(self, data: Optional[Dict[str, Any]] = None):
        return data or {}

    async def approve_timesheet(self, timesheet_id: Optional[int] = None):
        return {"timesheet_id": timesheet_id, "approved": True}

    def generate_report(self, **kwargs):
        return kwargs

    def create_entry(self, data: Optional[Dict[str, Any]] = None):
        return data or {}

    def get_summary(self, **kwargs):
        return kwargs

    def validate_entry(self, data: Optional[Dict[str, Any]] = None):
        return True

    def send_reminder(self, **kwargs):
        return kwargs or {"sent": True}


__all__ = ["TimesheetService"]
