# -*- coding: utf-8 -*-
"""
战略管理服务模块

提供 BEM 战略管理的完整业务逻辑实现，包括：
- 战略 CRUD 操作
- CSF/KPI 管理
- 健康度计算
- KPI 数据采集
- 目标分解
- 战略审视
- 同比分析
"""

# Strategy 服务
from .strategy_service import (
    archive_strategy,
    create_strategy,
    delete_strategy,
    get_active_strategy,
    get_strategy,
    get_strategy_by_code,
    get_strategy_by_year,
    get_strategy_detail,
    get_strategy_map_data,
    list_strategies,
    publish_strategy,
    update_strategy,
)

# CSF 服务
from .csf_service import (
    batch_create_csfs,
    create_csf,
    delete_csf,
    get_csf,
    get_csf_detail,
    get_csfs_by_dimension,
    list_csfs,
    update_csf,
)

# KPI 服务
from .kpi_service import (
    create_kpi,
    create_kpi_data_source,
    create_kpi_snapshot,
    delete_kpi,
    get_kpi,
    get_kpi_data_sources,
    get_kpi_detail,
    get_kpi_history,
    get_kpi_with_history,
    list_kpis,
    update_kpi,
    update_kpi_value,
)

# KPI 采集器
from .kpi_collector import (
    auto_collect_kpi,
    batch_collect_kpis,
    calculate_formula,
    collect_kpi_value,
    get_collection_status,
    get_collector,
    register_collector,
)

# 健康度计算
from .health_calculator import (
    calculate_csf_health,
    calculate_dimension_health,
    calculate_kpi_completion_rate,
    calculate_kpi_health,
    calculate_strategy_health,
    get_dimension_health_details,
    get_health_level,
    get_health_trend,
)

# 年度重点工作服务
from .annual_work_service import (
    calculate_progress_from_projects,
    create_annual_work,
    delete_annual_work,
    get_annual_work,
    get_annual_work_detail,
    get_annual_work_stats,
    get_linked_projects,
    link_project,
    list_annual_works,
    sync_progress_from_projects,
    unlink_project,
    update_annual_work,
    update_progress,
)

# 目标分解服务
from .decomposition_service import (
    batch_create_personal_kpis,
    create_department_objective,
    create_personal_kpi,
    delete_department_objective,
    delete_personal_kpi,
    get_decomposition_stats,
    get_decomposition_tree,
    get_department_objective,
    get_department_objective_detail,
    get_personal_kpi,
    list_department_objectives,
    list_personal_kpis,
    manager_rating,
    self_rating,
    trace_to_strategy,
    update_department_objective,
    update_personal_kpi,
)

# 战略审视服务
from .review_service import (
    create_calendar_event,
    create_strategy_review,
    delete_calendar_event,
    delete_strategy_review,
    generate_routine_events,
    get_calendar_event,
    get_calendar_month,
    get_calendar_year,
    get_health_score_summary,
    get_latest_review,
    get_routine_management_cycle,
    get_strategy_review,
    list_calendar_events,
    list_strategy_reviews,
    update_calendar_event,
    update_strategy_review,
)

# ��比分析服务
from .comparison_service import (
    create_strategy_comparison,
    delete_strategy_comparison,
    generate_yoy_report,
    get_kpi_achievement_comparison,
    get_multi_year_trend,
    get_strategy_comparison,
    list_strategy_comparisons,
)

__all__ = [
    # Strategy
    "create_strategy",
    "get_strategy",
    "get_strategy_by_code",
    "get_strategy_by_year",
    "get_active_strategy",
    "list_strategies",
    "update_strategy",
    "publish_strategy",
    "archive_strategy",
    "delete_strategy",
    "get_strategy_detail",
    "get_strategy_map_data",
    # CSF
    "create_csf",
    "get_csf",
    "list_csfs",
    "update_csf",
    "delete_csf",
    "get_csf_detail",
    "get_csfs_by_dimension",
    "batch_create_csfs",
    # KPI
    "create_kpi",
    "get_kpi",
    "list_kpis",
    "update_kpi",
    "delete_kpi",
    "update_kpi_value",
    "get_kpi_detail",
    "get_kpi_history",
    "get_kpi_with_history",
    "create_kpi_snapshot",
    "create_kpi_data_source",
    "get_kpi_data_sources",
    # KPI Collector
    "register_collector",
    "get_collector",
    "calculate_formula",
    "collect_kpi_value",
    "auto_collect_kpi",
    "batch_collect_kpis",
    "get_collection_status",
    # Health Calculator
    "calculate_kpi_completion_rate",
    "calculate_kpi_health",
    "calculate_csf_health",
    "calculate_dimension_health",
    "calculate_strategy_health",
    "get_health_level",
    "get_health_trend",
    "get_dimension_health_details",
    # Annual Work
    "create_annual_work",
    "get_annual_work",
    "list_annual_works",
    "update_annual_work",
    "delete_annual_work",
    "update_progress",
    "get_annual_work_detail",
    "link_project",
    "unlink_project",
    "get_linked_projects",
    "calculate_progress_from_projects",
    "sync_progress_from_projects",
    "get_annual_work_stats",
    # Decomposition
    "create_department_objective",
    "get_department_objective",
    "list_department_objectives",
    "update_department_objective",
    "delete_department_objective",
    "get_department_objective_detail",
    "create_personal_kpi",
    "get_personal_kpi",
    "list_personal_kpis",
    "update_personal_kpi",
    "delete_personal_kpi",
    "self_rating",
    "manager_rating",
    "batch_create_personal_kpis",
    "get_decomposition_tree",
    "trace_to_strategy",
    "get_decomposition_stats",
    # Review
    "create_strategy_review",
    "get_strategy_review",
    "list_strategy_reviews",
    "update_strategy_review",
    "delete_strategy_review",
    "get_latest_review",
    "get_health_score_summary",
    "create_calendar_event",
    "get_calendar_event",
    "list_calendar_events",
    "update_calendar_event",
    "delete_calendar_event",
    "get_calendar_month",
    "get_calendar_year",
    "get_routine_management_cycle",
    "generate_routine_events",
    # Comparison
    "create_strategy_comparison",
    "get_strategy_comparison",
    "list_strategy_comparisons",
    "delete_strategy_comparison",
    "generate_yoy_report",
    "get_multi_year_trend",
    "get_kpi_achievement_comparison",
]
