# -*- coding: utf-8 -*-
"""
预警相关任务配置
"""

ALERTING_TASKS = [
    {
        "id": "check_alert_escalation",
        "name": "预警升级服务",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_alert_escalation",
        "cron": {"minute": 10},
        "owner": "PMO",
        "category": "Alerting",
        "description": "每小时 +10 分处理预警升级逻辑。",
        "enabled": True,
        "dependencies_tables": ["alert_records"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 180,
            "retry_on_failure": True,
        },
    },
    {
        "id": "send_alert_notifications",
        "name": "消息推送服务",
        "module": "app.utils.scheduled_tasks",
        "callable": "send_alert_notifications",
        "cron": {"minute": 15},
        "owner": "PMO",
        "category": "Alerting",
        "description": "每小时 +15 分推送汇总消息（短信/企微等）。",
        "enabled": True,
        "dependencies_tables": ["alert_records", "users"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": True,
        },
    },
    {
        "id": "retry_failed_notifications",
        "name": "通知重试机制",
        "module": "app.utils.scheduled_tasks",
        "callable": "retry_failed_notifications",
        "cron": {"minute": 30},
        "owner": "PMO",
        "category": "Alerting",
        "description": "每小时 +30 分重试发送失败的通知。",
        "enabled": True,
        "dependencies_tables": ["alert_notifications", "alert_records", "users"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
    {
        "id": "calculate_response_metrics",
        "name": "计算响应时效指标",
        "module": "app.utils.scheduled_tasks",
        "callable": "calculate_response_metrics",
        "cron": {"hour": 1, "minute": 0},
        "owner": "Backend Platform",
        "category": "Alert Statistics",
        "description": "每天凌晨1点计算预警响应时效指标并更新统计表。",
        "enabled": True,
        "dependencies_tables": ["alert_records", "alert_statistics"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
]
