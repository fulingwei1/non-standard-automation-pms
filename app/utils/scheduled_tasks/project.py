# -*- coding: utf-8 -*-
"""
定时任务 - 项目管理模块

包含：项目健康度、里程碑、问题管理等任务
此文件作为聚合模块，从各个子模块导入实际实现
"""
import logging

logger = logging.getLogger(__name__)


# ==================== 项目健康度相关任务 ====================
# 从 project_health_tasks.py 导入
try:
    from app.utils.scheduled_tasks.project_health_tasks import (
        calculate_project_health,
        daily_health_snapshot,
    )
except ImportError:
    logger.warning("无法导入项目健康度任务，部分功能可能不可用")
    calculate_project_health = None
    daily_health_snapshot = None


# ==================== 问题管理定时任务 ====================
# 从 issue_tasks.py / issue_scheduled_tasks.py 导入
try:
    from app.utils.scheduled_tasks.issue_tasks import (
        check_blocking_issues,
        check_overdue_issues,
        check_timeout_issues,
        daily_issue_statistics_snapshot,
    )
except ImportError:
    try:
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_blocking_issues,
            check_overdue_issues,
            check_timeout_issues,
            daily_issue_statistics_snapshot,
        )
    except ImportError:
        logger.warning("无法导入问题管理任务，部分功能可能不可用")
        check_overdue_issues = None
        check_blocking_issues = None
        check_timeout_issues = None
        daily_issue_statistics_snapshot = None


# ==================== 里程碑相关任务 ====================
# 从 project_scheduled_tasks.py 导入
try:
    from app.utils.scheduled_tasks.project_scheduled_tasks import (
        check_milestone_alerts,
        check_milestone_risk_alerts,
        check_milestone_status_and_adjust_payments,
    )
except ImportError:
    logger.warning("无法导入里程碑任务，部分功能可能不可用")
    check_milestone_alerts = None
    check_milestone_status_and_adjust_payments = None
    check_milestone_risk_alerts = None


# ==================== 成本相关任务 ====================
try:
    from app.utils.scheduled_tasks.project_scheduled_tasks import (
        check_cost_overrun_alerts,
    )
except ImportError:
    logger.warning("无法导入成本任务，部分功能可能不可用")
    check_cost_overrun_alerts = None


# 导出所有任务函数
__all__ = [
    'calculate_project_health',
    'daily_health_snapshot',
    'check_overdue_issues',
    'check_blocking_issues',
    'check_timeout_issues',
    'daily_issue_statistics_snapshot',
    'check_milestone_alerts',
    'check_milestone_status_and_adjust_payments',
    'check_milestone_risk_alerts',
    'check_cost_overrun_alerts',
]
