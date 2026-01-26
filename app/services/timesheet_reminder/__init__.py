# -*- coding: utf-8 -*-
"""
工时提醒服务模块

提供工时填报提醒、异常工时预警、审批超时提醒等功能

模块结构:
 ├── base.py              # 基础工具函数
 ├── missing_reminders.py # 工时缺失提醒
 ├── anomaly_reminders.py # 异常工时预警
 ├── approval_reminders.py # 审批超时提醒
 ├── sync_reminders.py    # 同步失败提醒
 └── scanner.py           # 扫描器
"""

# 基础工具
from .base import (
    create_timesheet_notification,
)

# 工时缺失提醒
from .missing_reminders import (
    notify_timesheet_missing,
    notify_weekly_timesheet_missing,
)

# 异常工时预警
from .anomaly_reminders import (
    notify_timesheet_anomaly,
)

# 审批超时提醒
from .approval_reminders import (
    notify_approval_timeout,
)

# 同步失败提醒
from .sync_reminders import (
    notify_sync_failure,
)

# 扫描器
from .scanner import (
    scan_and_notify_all,
)

__all__ = [
    # 基础工具
    "create_timesheet_notification",
    # 工时缺失提醒
    "notify_timesheet_missing",
    "notify_weekly_timesheet_missing",
    # 异常工时预警
    "notify_timesheet_anomaly",
    # 审批超时提醒
    "notify_approval_timeout",
    # 同步失败提醒
    "notify_sync_failure",
    # 扫描器
    "scan_and_notify_all",
]
