# -*- coding: utf-8 -*-
"""
销售提醒服务模块
包含：关键节点提醒、逾期提醒、销售流程提醒
"""

from app.services.sales_reminder.base import (
    create_notification,
    find_users_by_department,
    find_users_by_role,
)
from app.services.sales_reminder.contract_reminders import (
    notify_contract_expiring,
    notify_contract_signed,
)
from app.services.sales_reminder.invoice_reminders import notify_invoice_issued
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
from app.services.sales_reminder.scanner import (
    scan_and_notify_all,
    scan_sales_reminders,
)

__all__ = [
    # Base utilities
    "find_users_by_role",
    "find_users_by_department",
    "create_notification",

    # Milestone reminders
    "notify_milestone_upcoming",
    "notify_milestone_overdue",

    # Payment reminders
    "notify_payment_plan_upcoming",
    "notify_payment_overdue",

    # Contract reminders
    "notify_contract_signed",
    "notify_contract_expiring",

    # Invoice reminders
    "notify_invoice_issued",

    # Sales flow reminders
    "notify_gate_timeout",
    "notify_quote_expiring",
    "notify_approval_pending",

    # Scanners
    "scan_and_notify_all",
    "scan_sales_reminders"
]
