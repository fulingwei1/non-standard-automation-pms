# -*- coding: utf-8 -*-
"""Compatibility imports for the legacy dashboard adapter package.

Dashboard adapters now live under ``app.services.dashboard.adapters``.  Some
routers and older tests still import ``app.services.dashboard_adapters``; keep
that path as a thin alias so importing it still triggers adapter registration.
"""

from importlib import import_module
import sys

from app.services.dashboard.adapters import *  # noqa: F401,F403

_ALIASES = {
    "assembly_kit": "app.services.dashboard.adapters.assembly_kit",
    "business_support": "app.services.dashboard.adapters.business_support",
    "dept_head_view": "app.services.dashboard.adapters.dept_head_view",
    "executive_view": "app.services.dashboard.adapters.executive_view",
    "hr_management": "app.services.dashboard.adapters.hr_management",
    "management_rhythm": "app.services.dashboard.adapters.management_rhythm",
    "member_view": "app.services.dashboard.adapters.member_view",
    "others": "app.services.dashboard.adapters.others",
    "pm_view": "app.services.dashboard.adapters.pm_view",
    "pmo": "app.services.dashboard.adapters.pmo",
    "presales": "app.services.dashboard.adapters.presales",
    "production": "app.services.dashboard.adapters.production",
    "shortage": "app.services.dashboard.adapters.shortage",
    "strategy": "app.services.dashboard.adapters.strategy",
}

for legacy_name, canonical_name in _ALIASES.items():
    module = import_module(canonical_name)
    sys.modules[f"{__name__}.{legacy_name}"] = module
    globals()[legacy_name] = module
