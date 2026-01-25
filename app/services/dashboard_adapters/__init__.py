# -*- coding: utf-8 -*-
"""
Dashboard 适配器模块

所有dashboard适配器的统一入口。
各模块的适配器会在导入时自动注册到全局registry中。
"""

# 导入所有适配器，触发自动注册
from app.services.dashboard_adapters.assembly_kit import (  # noqa: F401
    AssemblyKitDashboardAdapter,
)
from app.services.dashboard_adapters.business_support import (  # noqa: F401
    BusinessSupportDashboardAdapter,
)
from app.services.dashboard_adapters.hr_management import (  # noqa: F401
    HrDashboardAdapter,
)
from app.services.dashboard_adapters.management_rhythm import (  # noqa: F401
    ManagementRhythmDashboardAdapter,
)
from app.services.dashboard_adapters.others import (  # noqa: F401
    KitRateDashboardAdapter,
    StaffMatchingDashboardAdapter,
)
from app.services.dashboard_adapters.pmo import (  # noqa: F401
    PmoDashboardAdapter,
)
from app.services.dashboard_adapters.presales import (  # noqa: F401
    PresalesDashboardAdapter,
)
from app.services.dashboard_adapters.production import (  # noqa: F401
    ProductionDashboardAdapter,
)
from app.services.dashboard_adapters.shortage import (  # noqa: F401
    ShortageDashboardAdapter,
)
from app.services.dashboard_adapters.strategy import (  # noqa: F401
    StrategyDashboardAdapter,
)

__all__ = [
    "AssemblyKitDashboardAdapter",
    "BusinessSupportDashboardAdapter",
    "HrDashboardAdapter",
    "KitRateDashboardAdapter",
    "ManagementRhythmDashboardAdapter",
    "PmoDashboardAdapter",
    "PresalesDashboardAdapter",
    "ProductionDashboardAdapter",
    "ShortageDashboardAdapter",
    "StaffMatchingDashboardAdapter",
    "StrategyDashboardAdapter",
]
