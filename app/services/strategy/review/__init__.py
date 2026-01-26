# -*- coding: utf-8 -*-
"""
战略审视服务模块

提供战略审视与例行管理的完整业务逻辑

模块结构:
 ├── strategy_reviews.py    # 战略审视管理
 ├── health_summary.py      # 健康度汇总
 ├── calendar_events.py     # 战略日历管理
 └── routine_management.py  # 例行管理周期
"""

# 战略审视管理
from .strategy_reviews import (
    create_strategy_review,
    delete_strategy_review,
    get_latest_review,
    get_strategy_review,
    list_strategy_reviews,
    update_strategy_review,
)

# 健康度汇总
from .health_summary import (
    get_health_score_summary,
)

# 战略日历管理
from .calendar_events import (
    create_calendar_event,
    delete_calendar_event,
    get_calendar_event,
    get_calendar_month,
    get_calendar_year,
    list_calendar_events,
    update_calendar_event,
)

# 例行管理周期
from .routine_management import (
    generate_routine_events,
    get_routine_management_cycle,
)

__all__ = [
    # 战略审视管理
    "create_strategy_review",
    "get_strategy_review",
    "list_strategy_reviews",
    "update_strategy_review",
    "delete_strategy_review",
    "get_latest_review",
    # 健康度汇总
    "get_health_score_summary",
    # 战略日历管理
    "create_calendar_event",
    "get_calendar_event",
    "list_calendar_events",
    "update_calendar_event",
    "delete_calendar_event",
    "get_calendar_month",
    "get_calendar_year",
    # 例行管理周期
    "get_routine_management_cycle",
    "generate_routine_events",
]
