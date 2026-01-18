# -*- coding: utf-8 -*-
"""
ECN通知服务
功能：ECN相关通知的创建和发送

向后兼容：保持原有的函数接口
"""

from .approval_notifications import (
    notify_approval_assigned,
    notify_approval_result,
)
from .base import create_ecn_notification
from .ecn_notifications import (
    notify_ecn_submitted,
    notify_overdue_alert,
)
from .evaluation_notifications import (
    notify_evaluation_assigned,
    notify_evaluation_completed,
)
from .task_notifications import (
    notify_task_assigned,
    notify_task_completed,
)
from .utils import (
    check_all_evaluations_completed,
    find_department_manager,
    find_users_by_department,
    find_users_by_role,
)

# 向后兼容：导出所有原有函数
__all__ = [
    # 基础函数
    'create_ecn_notification',
    # 工具函数
    'find_users_by_department',
    'find_users_by_role',
    'find_department_manager',
    'check_all_evaluations_completed',
    # 评估通知
    'notify_evaluation_assigned',
    'notify_evaluation_completed',
    # 审批通知
    'notify_approval_assigned',
    'notify_approval_result',
    # 任务通知
    'notify_task_assigned',
    'notify_task_completed',
    # ECN通知
    'notify_ecn_submitted',
    'notify_overdue_alert',
]
