# -*- coding: utf-8 -*-
"""
里程碑任务配置
"""

MILESTONE_TASKS = [
    {
        "id": "check_milestone_alerts",
        "name": "里程碑到期预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_milestone_alerts",
        "cron": {"hour": 8, "minute": 0},
        "owner": "PMO",
        "category": "Milestone",
        "description": "每天早上8点检测里程碑到期预警（3天/1天分级）并推送通知。",
        "enabled": True,
        "dependencies_tables": ["project_milestones", "alert_records", "alert_notifications"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": True,
        },
    },
    {
        "id": "check_milestone_risk_alerts",
        "name": "里程碑风险前置识别",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_milestone_risk_alerts",
        "cron": {"hour": 8, "minute": 10},
        "owner": "PMO",
        "category": "Milestone",
        "description": "里程碑延期风险预测，基于进度/资源/前置里程碑多维指标评估并预警。",
        "enabled": True,
        "dependencies_tables": [
            "project_milestones",
            "projects",
            "pmo_project_phase",
            "alert_records",
            "alert_notifications",
        ],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
]
