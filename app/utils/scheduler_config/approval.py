# -*- coding: utf-8 -*-
"""通用审批引擎任务配置。"""

APPROVAL_TASKS = [
    {
        "id": "process_approval_timeout_warnings",
        "name": "审批即将超时预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "process_approval_timeout_warnings",
        "cron": {"minute": 30},
        "owner": "Backend Platform",
        "category": "Approval",
        "description": "每小时 30 分扫描即将超时的通用审批任务并发送预警。",
        "enabled": True,
        "dependencies_tables": [
            "approval_tasks",
            "approval_instances",
            "approval_node_definitions",
            "notifications",
        ],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": False,
        },
    },
    {
        "id": "process_approval_timeouts",
        "name": "审批超时自动处理",
        "module": "app.utils.scheduled_tasks",
        "callable": "process_approval_timeouts",
        "cron": {"minute": 0},
        "owner": "Backend Platform",
        "category": "Approval",
        "description": "整点扫描通用审批任务截止时间，执行 REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE。",
        "enabled": True,
        "dependencies_tables": [
            "approval_tasks",
            "approval_instances",
            "approval_node_definitions",
            "approval_action_logs",
            "users",
            "notifications",
        ],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
]
