# -*- coding: utf-8 -*-
"""
缺料管理任务配置
"""

SHORTAGE_TASKS = [
    {
        "id": "generate_shortage_alerts",
        "name": "缺料预警生成",
        "module": "app.utils.scheduled_tasks",
        "callable": "generate_shortage_alerts",
        "cron": {"hour": 7, "minute": 0},
        "owner": "Supply Chain",
        "category": "Shortage",
        "description": "每天 7 点生成缺料预警并更新 AlertRecord。",
        "enabled": True,
        "dependencies_tables": ["bom_items", "materials", "purchase_orders", "goods_receipts", "alert_records"],
        "risk_level": "CRITICAL",
        "sla": {
            "max_execution_time_seconds": 1200,
            "retry_on_failure": True,
        },
    },
    {
        "id": "auto_trigger_urgent_purchase_from_shortage_alerts",
        "name": "缺料预警自动触发紧急采购",
        "module": "app.utils.scheduled_tasks",
        "callable": "auto_trigger_urgent_purchase_from_shortage_alerts",
        "cron": {"hour": 7, "minute": 30},
        "owner": "Supply Chain",
        "category": "Shortage",
        "description": "每天 7:30 检查紧急级别的缺料预警，自动创建采购申请。",
        "enabled": True,
        "dependencies_tables": ["mat_shortage_alert", "materials", "material_suppliers", "purchase_requests"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
    {
        "id": "daily_kit_check",
        "name": "每日齐套检查",
        "module": "app.utils.scheduled_tasks",
        "callable": "daily_kit_check",
        "cron": {"hour": 6, "minute": 0},
        "owner": "Supply Chain",
        "category": "Shortage",
        "description": "每天 6 点计算物料齐套情况。",
        "enabled": True,
        "dependencies_tables": ["bom_items", "materials", "purchase_orders", "goods_receipts"],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 1200,
            "retry_on_failure": True,
        },
    },
    {
        "id": "generate_shortage_daily_report",
        "name": "缺料日报自动生成",
        "module": "app.utils.scheduled_tasks",
        "callable": "generate_shortage_daily_report",
        "cron": {"hour": 5, "minute": 15},
        "owner": "Supply Chain",
        "category": "Shortage",
        "description": "5:15 生成缺料日报供前端查询。",
        "enabled": True,
        "dependencies_tables": ["bom_items", "materials", "purchase_orders", "goods_receipts"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 1200,
            "retry_on_failure": False,
        },
    },
]
