# -*- coding: utf-8 -*-
"""
定时任务模块

本模块提供所有定时任务函数，包括：
- 基础设施和辅助函数
- 问题管理定时任务
- 里程碑和成本预警任务
- 工时提醒和汇总任务
- 销售/财务相关任务
- 其他杂项任务

原 scheduled_tasks.py 已拆分为多个子模块，此文件统一导出所有任务函数。
"""

# 基础模块
from .base import (
    send_notification_for_alert,
    generate_alert_no,
    logger,
)

# 问题管理任务
from .issue_tasks import (
    check_overdue_issues,
    check_blocking_issues,
    check_timeout_issues,
    daily_issue_statistics_snapshot,
    check_issue_timeout_escalation,
)

# 里程碑和成本任务
from .milestone_tasks import (
    check_milestone_alerts,
    check_milestone_status_and_adjust_payments,
    check_milestone_risk_alerts,
    check_cost_overrun_alerts,
)

# 工时任务
from .timesheet_tasks import (
    daily_timesheet_reminder_task,
    weekly_timesheet_reminder_task,
    timesheet_anomaly_alert_task,
    timesheet_approval_timeout_reminder_task,
    timesheet_sync_failure_alert_task,
    daily_timesheet_aggregation_task,
    weekly_timesheet_aggregation_task,
    monthly_timesheet_aggregation_task,
    generate_monthly_reports_task,
    calculate_monthly_labor_cost_task,
)

__all__ = [
    # 基础模块
    'send_notification_for_alert',
    'generate_alert_no',
    'logger',
    # 问题管理任务
    'check_overdue_issues',
    'check_blocking_issues',
    'check_timeout_issues',
    'daily_issue_statistics_snapshot',
    'check_issue_timeout_escalation',
    # 里程碑和成本任务
    'check_milestone_alerts',
    'check_milestone_status_and_adjust_payments',
    'check_milestone_risk_alerts',
    'check_cost_overrun_alerts',
    # 工时任务
    'daily_timesheet_reminder_task',
    'weekly_timesheet_reminder_task',
    'timesheet_anomaly_alert_task',
    'timesheet_approval_timeout_reminder_task',
    'timesheet_sync_failure_alert_task',
    'daily_timesheet_aggregation_task',
    'weekly_timesheet_aggregation_task',
    'monthly_timesheet_aggregation_task',
    'generate_monthly_reports_task',
    'calculate_monthly_labor_cost_task',
]
