# -*- coding: utf-8 -*-
"""
里程碑任务配置
"""

MILESTONE_TASKS = [
    {
        "id": "check_milestone_alerts",
        "name": "里程碑预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_milestone_alerts",
        "cron": {"hour": 8, "minute": 0},
        "owner": "PMO",
        "category": "Milestone",
        "description": "每天早上 8 点检测里程碑延期。",
        "enabled": True,
        "dependencies_tables": ["project_milestones", "alert_records"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": True,
        },
    },
    {
        "id": "check_milestone_risk_alerts",
        "name": "里程碑风险预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_milestone_risk_alerts",
        "cron": {"hour": 8, "minute": 10},
        "owner": "PMO",
        "category": "Milestone",
        "description": "里程碑风险版预警，比对多维指标。",
        "enabled": True,
        "dependencies_tables": ["project_milestones", "projects", "tasks", "alert_records"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
]
