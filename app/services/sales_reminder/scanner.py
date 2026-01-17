# -*- coding: utf-8 -*-
"""
销售提醒服务 - 扫描器
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.sales_reminder.contract_reminders import notify_contract_expiring
from app.services.sales_reminder.milestone_reminders import (
    notify_milestone_overdue,
    notify_milestone_upcoming,
)
from app.services.sales_reminder.payment_reminders import (
    notify_payment_overdue,
    notify_payment_plan_upcoming,
)
from app.services.sales_reminder.sales_flow_reminders import (
    notify_approval_pending,
    notify_gate_timeout,
    notify_quote_expiring,
)


def scan_and_notify_all(db: Session) -> dict:
    """
    扫描所有需要提醒的事项并发送通知
    返回统计信息
    """
    stats = {
        "milestone_upcoming_7d": 0,
        "milestone_upcoming_3d": 0,
        "milestone_overdue": 0,
        "payment_upcoming_7d": 0,
        "payment_upcoming_3d": 0,
        "payment_overdue": 0,
        # Sprint 3: 销售模块提醒
        "gate_timeout": 0,
        "quote_expiring": 0,
        "quote_expired": 0,
        "contract_expiring": 0,
        "approval_pending": 0
    }

    # 里程碑提醒（7天前）
    stats["milestone_upcoming_7d"] = notify_milestone_upcoming(db, days_before=7)

    # 里程碑提醒（3天前）
    stats["milestone_upcoming_3d"] = notify_milestone_upcoming(db, days_before=3)

    # 里程碑逾期
    stats["milestone_overdue"] = notify_milestone_overdue(db)

    # 收款计划提醒（7天前）
    stats["payment_upcoming_7d"] = notify_payment_plan_upcoming(db, days_before=7)

    # 收款计划提醒（3天前）
    stats["payment_upcoming_3d"] = notify_payment_plan_upcoming(db, days_before=3)

    # 收款逾期
    stats["payment_overdue"] = notify_payment_overdue(db)

    # Sprint 3: 销售模块提醒
    # 阶段门超时提醒
    stats["gate_timeout"] = notify_gate_timeout(db, settings.SALES_GATE_TIMEOUT_DAYS)

    # 报价过期提醒
    quote_stats = notify_quote_expiring(db)
    stats["quote_expiring"] = quote_stats.get("expiring", 0)
    stats["quote_expired"] = quote_stats.get("expired", 0)

    # 合同到期提醒
    stats["contract_expiring"] = notify_contract_expiring(db)

    # 审批待处理提醒
    stats["approval_pending"] = notify_approval_pending(db, settings.SALES_APPROVAL_TIMEOUT_HOURS)

    db.commit()

    return stats


def scan_sales_reminders(db: Session) -> dict:
    """
    扫描所有销售模块需要提醒的事项并发送通知
    返回统计信息
    """
    stats = {
        "gate_timeout": 0,
        "quote_expiring": 0,
        "quote_expired": 0,
        "contract_expiring": 0,
        "approval_pending": 0
    }

    # 阶段门超时提醒
    stats["gate_timeout"] = notify_gate_timeout(db, settings.SALES_GATE_TIMEOUT_DAYS)

    # 报价过期提醒
    quote_stats = notify_quote_expiring(db)
    stats["quote_expiring"] = quote_stats.get("expiring", 0)
    stats["quote_expired"] = quote_stats.get("expired", 0)

    # 合同到期提醒
    stats["contract_expiring"] = notify_contract_expiring(db)

    # 审批待处理提醒
    stats["approval_pending"] = notify_approval_pending(db, settings.SALES_APPROVAL_TIMEOUT_HOURS)

    db.commit()

    return stats
