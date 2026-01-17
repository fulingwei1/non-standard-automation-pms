# -*- coding: utf-8 -*-
"""
财务相关任务配置
"""

FINANCE_TASKS = [
    {
        "id": "check_cost_overrun_alerts",
        "name": "成本超支预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_cost_overrun_alerts",
        "cron": {"hour": 10, "minute": 0},
        "owner": "Finance",
        "category": "Cost",
        "description": "每天 10 点检查项目成本超支情况。",
        "enabled": True,
        "dependencies_tables": ["projects", "project_costs", "alert_records"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
    {
        "id": "calculate_monthly_labor_cost",
        "name": "月度工时成本计算",
        "module": "app.utils.scheduled_tasks",
        "callable": "calculate_monthly_labor_cost_task",
        "cron": {"day": 1, "hour": 2, "minute": 0},
        "owner": "Finance",
        "category": "Cost",
        "description": "每月1号凌晨2点自动计算上个月所有项目的人工成本。",
        "enabled": True,
        "dependencies_tables": ["timesheets", "projects", "project_costs"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 1800,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_payment_reminder",
        "name": "收款提醒服务",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_payment_reminder",
        "cron": {"hour": 9, "minute": 30},
        "owner": "Finance",
        "category": "Finance",
        "description": "9:30 发送即将收款的提醒。",
        "enabled": True,
        "dependencies_tables": ["project_payment_plans", "projects"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_overdue_receivable_alerts",
        "name": "逾期应收预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_overdue_receivable_alerts",
        "cron": {"hour": 10, "minute": 30},
        "owner": "Finance",
        "category": "Finance",
        "description": "10:30 检查逾期应收账款。",
        "enabled": True,
        "dependencies_tables": ["project_payment_plans", "projects", "alert_records"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
]
