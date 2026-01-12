# -*- coding: utf-8 -*-
"""
定时任务模块

本模块提供所有定时任务函数，按功能分类：
- base.py: 基础设施和辅助函数
- issue_tasks.py: 问题管理定时任务
- milestone_tasks.py: 里程碑和成本预警任务
- timesheet_tasks.py: 工时提醒和汇总任务
- alert_tasks.py: P0预警服务任务
- sales_tasks.py: 销售/财务相关任务
- notification_tasks.py: 通知和杂项任务

原 scheduled_tasks.py 已拆分到以上模块，此文件统一导出所有任务函数。
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

# P0预警任务
from .alert_tasks import (
    generate_shortage_alerts,
    check_task_delay_alerts,
    check_production_plan_alerts,
    check_work_report_timeout,
    calculate_progress_summary,
    daily_kit_check,
    check_delivery_delay,
    check_task_deadline_reminder,
    check_outsourcing_delivery_alerts,
)

# 销售/财务任务
from .sales_tasks import (
    sales_reminder_scan,
    check_payment_reminder,
    check_overdue_receivable_alerts,
    check_opportunity_stage_timeout,
    check_presale_workorder_timeout,
    check_contract_expiry_reminder,
)

# 通知和杂项任务
from .notification_tasks import (
    check_alert_escalation,
    retry_failed_notifications,
    send_alert_notifications,
    calculate_response_metrics,
    check_equipment_maintenance_reminder,
    check_employee_confirmation_reminder,
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
    # P0预警任务
    'generate_shortage_alerts',
    'check_task_delay_alerts',
    'check_production_plan_alerts',
    'check_work_report_timeout',
    'calculate_progress_summary',
    'daily_kit_check',
    'check_delivery_delay',
    'check_task_deadline_reminder',
    'check_outsourcing_delivery_alerts',
    # 销售/财务任务
    'sales_reminder_scan',
    'check_payment_reminder',
    'check_overdue_receivable_alerts',
    'check_opportunity_stage_timeout',
    'check_presale_workorder_timeout',
    'check_contract_expiry_reminder',
    # 通知和杂项任务
    'check_alert_escalation',
    'retry_failed_notifications',
    'send_alert_notifications',
    'calculate_response_metrics',
    'check_equipment_maintenance_reminder',
    'check_employee_confirmation_reminder',
]
