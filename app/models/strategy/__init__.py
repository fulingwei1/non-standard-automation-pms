# -*- coding: utf-8 -*-
"""
战略管理模块模型 - 按功能域聚合
"""

# 核心模型
from .core import (
    CSF,
    KPI,
    KPIDataSource,
    KPIHistory,
    Strategy,
)

# 年度重点工作
from .annual_work import (
    AnnualKeyWork,
    AnnualKeyWorkProjectLink,
)

# 目标分解
from .decomposition import (
    DepartmentObjective,
    PersonalKPI,
)

# 战略审视
from .review import (
    StrategyCalendarEvent,
    StrategyReview,
)

# 战略对比
from .comparison import (
    StrategyComparison,
)

__all__ = [
    # 核心
    "Strategy",
    "CSF",
    "KPI",
    "KPIHistory",
    "KPIDataSource",
    # 年度重点工作
    "AnnualKeyWork",
    "AnnualKeyWorkProjectLink",
    # 目标分解
    "DepartmentObjective",
    "PersonalKPI",
    # 战略审视
    "StrategyReview",
    "StrategyCalendarEvent",
    # 战略对比
    "StrategyComparison",
]
