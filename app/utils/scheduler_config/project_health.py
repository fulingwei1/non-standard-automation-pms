# -*- coding: utf-8 -*-
"""
项目健康度任务配置
"""

PROJECT_HEALTH_TASKS = [
    {
        "id": "calculate_project_health",
        "name": "计算项目健康度",
        "module": "app.utils.scheduled_tasks",
        "callable": "calculate_project_health",
        "cron": {"minute": 0},
        "owner": "Backend Platform",
        "category": "Project Health",
        "description": "每小时为所有活跃项目重新计算健康度并写入项目表。",
        "enabled": True,
        "dependencies_tables": ["projects", "project_milestones", "issues", "alert_records", "tasks"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
    {
        "id": "daily_health_snapshot",
        "name": "每日健康度快照",
        "module": "app.utils.scheduled_tasks",
        "callable": "daily_health_snapshot",
        "cron": {"hour": 2, "minute": 0},
        "owner": "Backend Platform",
        "category": "Project Health",
        "description": "凌晨 2 点为活跃项目生成健康度快照记录。",
        "enabled": True,
        "dependencies_tables": ["projects", "project_health_snapshots"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": False,
        },
    },
]
