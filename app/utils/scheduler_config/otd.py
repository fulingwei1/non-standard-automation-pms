# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 - 调度任务元数据

每天 07:00 执行 OTD 全量扫描，排在 06:00 项目风险计算之后。
"""

OTD_TASKS = [
    {
        "id": "daily_otd_scan",
        "name": "OTD 项目交付每日风险扫描",
        "module": "app.utils.scheduled_tasks",
        "callable": "daily_otd_scan",
        "cron": {"hour": 7, "minute": 0},  # 每天 07:00（排在 06:00 风险计算之后）
        "owner": "Backend Platform",
        "category": "OTD Delivery",
        "description": (
            "每天扫描执行中项目（生命周期 S2~S8）的 10 维 OTD 交付风险"
            "（采购延期/图纸未冻结/客户变更频繁/BOM超预算/调试反复/"
            "验收资料缺失/回款条件不齐/关键节点延期/进度滞后/毛利偏差），"
            "对 HIGH/CRITICAL 项目产出预警并推送项目经理。"
        ),
        "enabled": True,
        "dependencies_tables": [
            "projects",
            "project_milestones",
            "project_payment_plans",
            "purchase_orders",
            "purchase_order_items",
            "change_requests",
            "issues",
            "acceptance_orders",
            "acceptance_order_items",
            "technical_reviews",
            "alert_records",
        ],
        "risk_level": "HIGH",
        "sla": {
            "max_execution_time_seconds": 900,
            "retry_on_failure": True,
        },
    },
    {
        "id": "daily_margin_snapshot",
        "name": "毛利率每日快照",
        "module": "app.utils.scheduled_tasks",
        "callable": "daily_margin_snapshot",
        "cron": {"hour": 7, "minute": 30},  # 排在 OTD 07:00 之后
        "owner": "Backend Platform",
        "category": "Margin Dashboard",
        "description": (
            "每天为活跃项目落毛利率快照，用于毛利率 Dashboard 趋势分析。"
            "复用 ProfitAnalysisService.get_margin_analysis。"
        ),
        "enabled": True,
        "dependencies_tables": ["projects", "project_margin_snapshots"],
        "risk_level": "MEDIUM",
        "sla": {
            "max_execution_time_seconds": 600,
            "retry_on_failure": True,
        },
    },
]
