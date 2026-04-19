# -*- coding: utf-8 -*-
"""向后兼容 re-export：dashboard adapter 现已位于 app.services.dashboard.dashboard_adapter。"""

from app.services.dashboard.dashboard_adapter import (  # noqa: F401
    DashboardAdapter,
    DashboardRegistry,
    dashboard_registry,
    register_dashboard,
)

__all__ = [
    "DashboardAdapter",
    "DashboardRegistry",
    "dashboard_registry",
    "register_dashboard",
]
