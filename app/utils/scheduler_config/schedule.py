# -*- coding: utf-8 -*-
"""
进度和任务调度配置
"""

SCHEDULE_TASKS = [
    {
        "id": "check_task_delay_alerts",
        "name": "任务延期预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_task_delay_alerts",
        "cron": {"minute": 0},
        "owner": "PMO",
        "category": "Schedule",
        "description": "整点检查计划任务延期情况。",
        "enabled": True,
        "dependencies_tables": ["tasks", "alert_records"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 180,
            "retry_on_failure": True,
        },
    },
    {
        "id": "calculate_progress_summary",
        "name": "进度汇总计算",
        "module": "app.utils.scheduled_tasks",
        "callable": "calculate_progress_summary",
        "cron": {"minute": 0},
        "owner": "PMO",
        "category": "Schedule",
        "description": "整点计算项目/任务进度汇总数据。",
        "enabled": True,
        "dependencies_tables": ["projects", "tasks"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_task_deadline_reminder",
        "name": "任务到期提醒",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_task_deadline_reminder",
        "cron": {"minute": 0},
        "owner": "PMO",
        "category": "Schedule",
        "description": "整点提醒即将到期的任务负责人。",
        "enabled": True,
        "dependencies_tables": ["tasks", "users"],
        "risk_level": "LOW",
        "sla": {
            "max_execution_time_seconds": 120,
            "retry_on_failure": False,
        },
    },
]
