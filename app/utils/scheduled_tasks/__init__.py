# -*- coding: utf-8 -*-
"""
定时任务调度中心
统一导出和管理所有业务域的定时任务

模块结构:
├── base.py                    # 通用辅助函数
├── sales_tasks.py             # 销售相关任务
├── project_health_tasks.py    # 项目健康度任务
├── project_scheduled_tasks.py # 项目定时任务(系统生成)
├── issue_tasks.py             # 问题管理任务
├── issue_scheduled_tasks.py   # 问题定时任务(系统生成)
├── milestone_tasks.py         # 里程碑任务
├── timesheet_tasks.py         # 工时任务
├── production_tasks.py        # 生产任务
├── alert_tasks.py             # 预警与通知任务
└── hr_tasks.py                # HR任务
"""
import logging

logger = logging.getLogger(__name__)

# ==================== 预警与通知任务 ====================
from .alert_tasks import (
    calculate_response_metrics,
    check_alert_escalation,
    retry_failed_notifications,
    send_alert_notifications,
)

# ==================== 基础模块 ====================
from .base import (
    log_task_result,
    safe_task_execution,
    send_notification_for_alert,
)

# ==================== HR任务 ====================
from .hr_tasks import (
    check_contract_expiry_reminder,
    check_employee_confirmation_reminder,
)

# ==================== 齐套率任务 ====================
from .kit_rate_tasks import (
    create_kit_rate_snapshot,
    create_stage_change_snapshot,
    daily_kit_rate_snapshot,
)

# ==================== 问题管理任务 ====================
from .issue_scheduled_tasks import (
    check_blocking_issues,
    check_issue_assignment_timeout,
    check_issue_resolution_timeout,
    check_overdue_issues,
    check_timeout_issues,
    daily_issue_statistics_snapshot,
)

# ==================== 里程碑任务 ====================
from .milestone_tasks import (
    check_milestone_alerts,
    check_milestone_risk_alerts,
    check_milestone_status_and_adjust_payments,
)

# ==================== 生产任务 ====================
from .production_tasks import (
    check_production_plan_alerts,
    check_work_report_timeout,
    generate_production_daily_reports,
)

# ==================== 项目管理任务 ====================
from .project_scheduled_tasks import (
    calculate_progress_summary,
    calculate_project_health,
    check_project_cost_overrun,
    check_project_deadline_alerts,
    daily_health_snapshot,
    daily_spec_match_check,
)

# ==================== 销售任务 ====================
from .sales_tasks import (
    check_opportunity_stage_timeout,
    check_overdue_receivable_alerts,
    check_payment_reminder,
    sales_reminder_scan,
)

# ==================== 工时任务 ====================
from .timesheet_tasks import (
    calculate_monthly_labor_cost_task,
    daily_timesheet_aggregation_task,
    daily_timesheet_reminder_task,
    monthly_timesheet_aggregation_task,
    timesheet_anomaly_alert_task,
    timesheet_approval_timeout_reminder_task,
    timesheet_sync_failure_alert_task,
    weekly_timesheet_aggregation_task,
    weekly_timesheet_reminder_task,
)

# ==================== 任务注册表 ====================
SCHEDULED_TASKS = {
    # 项目管理任务
    'daily_spec_match_check': daily_spec_match_check,
    'calculate_project_health': calculate_project_health,
    'daily_health_snapshot': daily_health_snapshot,
    'calculate_progress_summary': calculate_progress_summary,
    'check_project_deadline_alerts': check_project_deadline_alerts,
    'check_project_cost_overrun': check_project_cost_overrun,

    # 问题管理任务
    'check_overdue_issues': check_overdue_issues,
    'check_blocking_issues': check_blocking_issues,
    'check_timeout_issues': check_timeout_issues,
    'daily_issue_statistics_snapshot': daily_issue_statistics_snapshot,
    'check_issue_assignment_timeout': check_issue_assignment_timeout,
    'check_issue_resolution_timeout': check_issue_resolution_timeout,

    # 销售任务
    'sales_reminder_scan': sales_reminder_scan,
    'check_payment_reminder': check_payment_reminder,
    'check_overdue_receivable_alerts': check_overdue_receivable_alerts,
    'check_opportunity_stage_timeout': check_opportunity_stage_timeout,

    # 里程碑任务
    'check_milestone_alerts': check_milestone_alerts,
    'check_milestone_status_and_adjust_payments': check_milestone_status_and_adjust_payments,
    'check_milestone_risk_alerts': check_milestone_risk_alerts,

    # 工时任务
    'daily_timesheet_reminder_task': daily_timesheet_reminder_task,
    'weekly_timesheet_reminder_task': weekly_timesheet_reminder_task,
    'timesheet_anomaly_alert_task': timesheet_anomaly_alert_task,
    'timesheet_approval_timeout_reminder_task': timesheet_approval_timeout_reminder_task,
    'timesheet_sync_failure_alert_task': timesheet_sync_failure_alert_task,
    'daily_timesheet_aggregation_task': daily_timesheet_aggregation_task,
    'weekly_timesheet_aggregation_task': weekly_timesheet_aggregation_task,
    'monthly_timesheet_aggregation_task': monthly_timesheet_aggregation_task,
    'calculate_monthly_labor_cost_task': calculate_monthly_labor_cost_task,

    # 生产任务
    'check_production_plan_alerts': check_production_plan_alerts,
    'check_work_report_timeout': check_work_report_timeout,
    'generate_production_daily_reports': generate_production_daily_reports,

    # 预警与通知任务
    'check_alert_escalation': check_alert_escalation,
    'retry_failed_notifications': retry_failed_notifications,
    'send_alert_notifications': send_alert_notifications,
    'calculate_response_metrics': calculate_response_metrics,

    # HR任务
    'check_contract_expiry_reminder': check_contract_expiry_reminder,
    'check_employee_confirmation_reminder': check_employee_confirmation_reminder,

    # 齐套率任务
    'daily_kit_rate_snapshot': daily_kit_rate_snapshot,
}

# ==================== 任务分组 ====================
TASK_GROUPS = {
    'project': {
        'name': '项目管理',
        'tasks': [
            'daily_spec_match_check',
            'calculate_project_health',
            'daily_health_snapshot',
            'calculate_progress_summary',
            'check_project_deadline_alerts',
            'check_project_cost_overrun',
        ]
    },
    'issue': {
        'name': '问题管理',
        'tasks': [
            'check_overdue_issues',
            'check_blocking_issues',
            'check_timeout_issues',
            'daily_issue_statistics_snapshot',
            'check_issue_assignment_timeout',
            'check_issue_resolution_timeout',
        ]
    },
    'sales': {
        'name': '销售管理',
        'tasks': [
            'sales_reminder_scan',
            'check_payment_reminder',
            'check_overdue_receivable_alerts',
            'check_opportunity_stage_timeout',
        ]
    },
    'milestone': {
        'name': '里程碑管理',
        'tasks': [
            'check_milestone_alerts',
            'check_milestone_status_and_adjust_payments',
            'check_milestone_risk_alerts',
        ]
    },
    'timesheet': {
        'name': '工时管理',
        'tasks': [
            'daily_timesheet_reminder_task',
            'weekly_timesheet_reminder_task',
            'timesheet_anomaly_alert_task',
            'timesheet_approval_timeout_reminder_task',
            'timesheet_sync_failure_alert_task',
            'daily_timesheet_aggregation_task',
            'weekly_timesheet_aggregation_task',
            'monthly_timesheet_aggregation_task',
            'calculate_monthly_labor_cost_task',
        ]
    },
    'production': {
        'name': '生产管理',
        'tasks': [
            'check_production_plan_alerts',
            'check_work_report_timeout',
            'generate_production_daily_reports',
        ]
    },
    'alert': {
        'name': '预警通知',
        'tasks': [
            'check_alert_escalation',
            'retry_failed_notifications',
            'send_alert_notifications',
            'calculate_response_metrics',
        ]
    },
    'hr': {
        'name': '人力资源',
        'tasks': [
            'check_contract_expiry_reminder',
            'check_employee_confirmation_reminder',
        ]
    },
    'kit_rate': {
        'name': '齐套率管理',
        'tasks': [
            'daily_kit_rate_snapshot',
        ]
    },
}


# ==================== 工具函数 ====================
def get_task(task_name: str):
    """获取指定名称的定时任务函数"""
    return SCHEDULED_TASKS.get(task_name)


def get_tasks_by_group(group_name: str) -> dict:
    """获取指定业务域的所有定时任务"""
    group = TASK_GROUPS.get(group_name)
    if not group:
        return {}

    return {
        task_name: SCHEDULED_TASKS.get(task_name)
        for task_name in group['tasks']
        if task_name in SCHEDULED_TASKS
    }


def list_all_tasks() -> list:
    """列出所有可用的定时任务"""
    task_info = []
    for group_name, group_info in TASK_GROUPS.items():
        for task_name in group_info['tasks']:
            task_info.append({
                'name': task_name,
                'group': group_name,
                'group_name': group_info['name'],
                'function': SCHEDULED_TASKS.get(task_name)
            })
    return task_info


def execute_task(task_name: str, *args, **kwargs):
    """执行指定的定时任务"""
    task_func = get_task(task_name)
    if task_func is None:
        raise ValueError(f"定时任务 '{task_name}' 不存在")

    try:
        return task_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"执行定时任务 '{task_name}' 失败: {str(e)}")
        raise


# ==================== 导出 ====================
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

    # 齐套率
    'daily_kit_rate_snapshot',
    'create_kit_rate_snapshot',
    'create_stage_change_snapshot',
]
