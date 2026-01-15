# -*- coding: utf-8 -*-
"""
定时任务模块 - 兼容层
==================

注意：此文件已重构为模块化结构，原3845行代码已拆分至 scheduled_tasks/ 目录。
此文件保留用于向后兼容，所有导入将从新模块重导出。

新结构:
├── scheduled_tasks/
│   ├── __init__.py              # 统一导出
│   ├── base.py                  # 通用辅助函数
│   ├── sales_tasks.py           # 销售任务
│   ├── project_scheduled_tasks.py # 项目管理任务
│   ├── issue_scheduled_tasks.py   # 问题管理任务
│   ├── milestone_tasks.py       # 里程碑任务
│   ├── timesheet_tasks.py       # 工时任务
│   ├── production_tasks.py      # 生产任务
│   ├── alert_tasks.py           # 预警通知任务
│   └── hr_tasks.py              # HR任务

推荐迁移:
    # 旧方式 (此文件):
    from app.utils.scheduled_tasks import sales_reminder_scan

    # 新方式 (推荐):
    from app.utils.scheduled_tasks import sales_reminder_scan
    # 或按业务域导入:
    from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan
"""
import warnings

# 发出弃用警告（仅在直接导入此文件时）
warnings.warn(
    "直接从 app.utils.scheduled_tasks 导入即将弃用，"
    "建议从 app.utils.scheduled_tasks 包或其子模块导入。",
    DeprecationWarning,
    stacklevel=2
)

# 从新模块结构重导出所有内容
from app.utils.scheduled_tasks import (
    # 配置
    SCHEDULED_TASKS,
    TASK_GROUPS,

    # 工具函数
    get_task,
    get_tasks_by_group,
    list_all_tasks,
    execute_task,

    # 基础函数
    send_notification_for_alert,
    log_task_result,
    safe_task_execution,

    # 项目管理
    daily_spec_match_check,
    calculate_project_health,
    daily_health_snapshot,
    calculate_progress_summary,
    check_project_deadline_alerts,
    check_project_cost_overrun,

    # 问题管理
    check_overdue_issues,
    check_blocking_issues,
    check_timeout_issues,
    daily_issue_statistics_snapshot,
    check_issue_assignment_timeout,
    check_issue_resolution_timeout,

    # 销售
    sales_reminder_scan,
    check_payment_reminder,
    check_overdue_receivable_alerts,
    check_opportunity_stage_timeout,

    # 里程碑
    check_milestone_alerts,
    check_milestone_status_and_adjust_payments,
    check_milestone_risk_alerts,

    # 工时
    daily_timesheet_reminder_task,
    weekly_timesheet_reminder_task,
    timesheet_anomaly_alert_task,
    timesheet_approval_timeout_reminder_task,
    timesheet_sync_failure_alert_task,
    daily_timesheet_aggregation_task,
    weekly_timesheet_aggregation_task,
    monthly_timesheet_aggregation_task,
    calculate_monthly_labor_cost_task,

    # 生产
    check_production_plan_alerts,
    check_work_report_timeout,
    generate_production_daily_reports,

    # 预警通知
    check_alert_escalation,
    retry_failed_notifications,
    send_alert_notifications,
    calculate_response_metrics,

    # HR
    check_contract_expiry_reminder,
    check_employee_confirmation_reminder,
)

# 保持 __all__ 与新模块一致
__all__ = [
    # 配置
    'SCHEDULED_TASKS',
    'TASK_GROUPS',

    # 工具函数
    'get_task',
    'get_tasks_by_group',
    'list_all_tasks',
    'execute_task',

    # 基础函数
    'send_notification_for_alert',
    'log_task_result',
    'safe_task_execution',

    # 项目管理
    'daily_spec_match_check',
    'calculate_project_health',
    'daily_health_snapshot',
    'calculate_progress_summary',
    'check_project_deadline_alerts',
    'check_project_cost_overrun',

    # 问题管理
    'check_overdue_issues',
    'check_blocking_issues',
    'check_timeout_issues',
    'daily_issue_statistics_snapshot',
    'check_issue_assignment_timeout',
    'check_issue_resolution_timeout',

    # 销售
    'sales_reminder_scan',
    'check_payment_reminder',
    'check_overdue_receivable_alerts',
    'check_opportunity_stage_timeout',

    # 里程碑
    'check_milestone_alerts',
    'check_milestone_status_and_adjust_payments',
    'check_milestone_risk_alerts',

    # 工时
    'daily_timesheet_reminder_task',
    'weekly_timesheet_reminder_task',
    'timesheet_anomaly_alert_task',
    'timesheet_approval_timeout_reminder_task',
    'timesheet_sync_failure_alert_task',
    'daily_timesheet_aggregation_task',
    'weekly_timesheet_aggregation_task',
    'monthly_timesheet_aggregation_task',
    'calculate_monthly_labor_cost_task',

    # 生产
    'check_production_plan_alerts',
    'check_work_report_timeout',
    'generate_production_daily_reports',

    # 预警通知
    'check_alert_escalation',
    'retry_failed_notifications',
    'send_alert_notifications',
    'calculate_response_metrics',

    # HR
    'check_contract_expiry_reminder',
    'check_employee_confirmation_reminder',
]
