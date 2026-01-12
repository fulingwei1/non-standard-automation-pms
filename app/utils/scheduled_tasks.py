# -*- coding: utf-8 -*-
"""
定时任务 - 兼容层

本文件现为兼容层，所有实现已迁移至 app/utils/tasks/ 模块。
为保持向后兼容，从 tasks 包统一导出所有函数。

新代码请直接使用:
    from app.utils.tasks import function_name
或:
    from app.utils.tasks.module_name import function_name
"""

# 从 tasks 包导出所有函数
from app.utils.tasks import (
    # 基础模块
    send_notification_for_alert,
    generate_alert_no,
    logger,
    # 规格匹配任务
    daily_spec_match_check,
    # 项目健康度任务
    calculate_project_health,
    daily_health_snapshot,
    # 问题管理任务
    check_overdue_issues,
    check_blocking_issues,
    check_timeout_issues,
    daily_issue_statistics_snapshot,
    check_issue_timeout_escalation,
    # 里程碑和成本任务
    check_milestone_alerts,
    check_milestone_status_and_adjust_payments,
    check_milestone_risk_alerts,
    check_cost_overrun_alerts,
    # 工时任务
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
    # P0预警任务
    generate_shortage_alerts,
    check_task_delay_alerts,
    check_production_plan_alerts,
    check_work_report_timeout,
    calculate_progress_summary,
    daily_kit_check,
    check_delivery_delay,
    check_task_deadline_reminder,
    check_outsourcing_delivery_alerts,
    # 销售/财务任务
    sales_reminder_scan,
    check_payment_reminder,
    check_overdue_receivable_alerts,
    check_opportunity_stage_timeout,
    check_presale_workorder_timeout,
    check_contract_expiry_reminder,
    # 通知和杂项任务
    check_alert_escalation,
    retry_failed_notifications,
    send_alert_notifications,
    calculate_response_metrics,
    check_equipment_maintenance_reminder,
    check_employee_confirmation_reminder,
    # 生产和资源任务
    generate_production_daily_reports,
    generate_shortage_daily_report,
    generate_job_duty_tasks,
    check_workload_overload_alerts,
)

__all__ = [
    # 基础模块
    'send_notification_for_alert',
    'generate_alert_no',
    'logger',
    # 规格匹配任务
    'daily_spec_match_check',
    # 项目健康度任务
    'calculate_project_health',
    'daily_health_snapshot',
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
    # 生产和资源任务
    'generate_production_daily_reports',
    'generate_shortage_daily_report',
    'generate_job_duty_tasks',
    'check_workload_overload_alerts',
]
