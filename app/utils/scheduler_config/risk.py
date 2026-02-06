# -*- coding: utf-8 -*-
"""
项目风险任务配置

包含：
1. 批量计算所有活跃项目的风险等级（每天执行）
2. 创建风险快照用于趋势分析（每天执行）
3. 检查高风险项目并生成预警（每4小时执行）
"""

RISK_TASKS = [
    {
        "id": "calculate_all_project_risks",
        "name": "批量计算项目风险等级",
        "module": "app.utils.scheduled_tasks",
        "callable": "calculate_all_project_risks",
        "cron": {"hour": 6, "minute": 0},  # 每天早上6点执行
        "owner": "Backend Platform",
        "category": "Project Risk",
        "description": "每天早上6点批量计算所有活跃项目的风险等级，检测风险升级并记录历史。",
        "enabled": True,
        "dependencies_tables": [
            "projects",
            "project_milestones",
            "pmo_project_risks",
            "project_risk_history",
        ],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
    {
        "id": "create_daily_risk_snapshots",
        "name": "创建每日风险快照",
        "module": "app.utils.scheduled_tasks",
        "callable": "create_daily_risk_snapshots",
        "cron": {"hour": 2, "minute": 30},  # 每天凌晨2:30执行
        "owner": "Backend Platform",
        "category": "Project Risk",
        "description": "每天凌晨2:30为所有活跃项目创建风险状态快照，用于趋势分析和报表生成。",
        "enabled": True,
        "dependencies_tables": [
            "projects",
            "project_risk_snapshot",
        ],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": False,
        },
    },
    {
        "id": "check_high_risk_projects",
        "name": "检查高风险项目预警",
        "module": "app.utils.scheduled_tasks",
        "callable": "check_high_risk_projects",
        "cron": {"hour": "*/4", "minute": 15},  # 每4小时执行一次（0:15, 4:15, 8:15...）
        "owner": "Backend Platform",
        "category": "Project Risk",
        "description": "每4小时检查风险等级为HIGH或CRITICAL的项目，生成预警通知相关人员。",
        "enabled": True,
        "dependencies_tables": [
            "projects",
            "project_risk_history",
            "alert_records",
        ],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 300,
            "retry_on_failure": True,
        },
    },
]
