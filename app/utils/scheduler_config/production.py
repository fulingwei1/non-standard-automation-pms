# -*- coding: utf-8 -*-
"""
生产相关任务配置
"""

PRODUCTION_TASKS = [
    {
        "id": "check_production_plan_alerts",
        "name": "生产计划预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_production_plan_alerts",
        "cron": {"hour": 11, "minute": 0},
        "owner": "Manufacturing",
        "category": "Production",
        "description": "每天 11 点评估生产计划执行偏差。",
        "enabled": True,
        "dependencies_tables": ["production_plans", "machines", "alert_records"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_work_report_timeout",
        "name": "报工超时提醒",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_work_report_timeout",
        "cron": {"minute": 0},
        "owner": "Manufacturing",
        "category": "Production",
        "description": "整点提醒未按时提交报工的人员。",
        "enabled": True,
        "dependencies_tables": ["timesheets", "users"],
        "risk_level": "LOW",
        "sla": {
            "max_execution_time_seconds": 120,
            "retry_on_failure": False,
        },
    },
    {
        "id": "generate_production_daily_reports",
        "name": "生产日报自动生成",
        "module": "app.utils.scheduled_tasks",
        "callable": "generate_production_daily_reports",
        "cron": {"hour": 5, "minute": 0},
        "owner": "Manufacturing",
        "category": "Production",
        "description": "凌晨 5 点自动生成生产日报数据。",
        "enabled": True,
        "dependencies_tables": ["production_plans", "machines", "timesheets"],
        "risk_level": "LOW",
        "sla": {
            "max_execution_time_seconds": 900,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_equipment_maintenance_reminder",
        "name": "设备保养提醒服务",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_equipment_maintenance_reminder",
        "cron": {"hour": 8, "minute": 30},
        "owner": "Manufacturing",
        "category": "Equipment",
        "description": "8:30 提醒设备保养计划。",
        "enabled": True,
        "dependencies_tables": ["machines", "equipment_maintenance_plans"],
        "risk_level": "LOW",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
]
