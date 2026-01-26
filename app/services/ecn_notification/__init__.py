# -*- coding: utf-8 -*-
"""
ECN通知服务（使用统一NotificationService）
功能：ECN相关通知的创建和发送

向后兼容：保持原有的函数接口，内部使用新的统一NotificationService
"""

from .base import create_ecn_notification
from .utils import (
    check_all_evaluations_completed,
    find_department_manager,
    find_users_by_department,
    find_users_by_role,
)

# 导入统一通知服务
from app.services.unified_notification_service import (
    NotificationService,
    NotificationChannel,
    NotificationPriority,
    notification_service,
)
from app.models.ecn import Ecn

# 便捷方法：使用统一NotificationService的快捷函数


def notify_ecn_submitted(db, ecn_id: int, ecn_number: str, submitter_name: str):
    """发送ECN提交通知（使用统一服务）"""
    service = notification_service(db)
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    return service.send_ecn_submitted(
        recipient_id=ecn.applicant_id if ecn else None,
        ecn_id=ecn_id,
        ecn_number=ecn_number,
        submitter_name=submitter_name,
    )


def notify_overdue_alert(
    db, ecn_id: int, ecn_number: str, days_overdue: int, days_remaining: int
):
    """发送ECN逾期预警（使用统一服务）"""
    service = notification_service(db)
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    return service.send_notification(
        {
            "recipient_id": ecn.applicant_id if ecn else None,
            "notification_type": "ECN_OVERDUE",
            "category": "ecn",
            "title": "ECN逾期提醒",
            "content": f"ECN {ecn_number} 已逾期{days_overdue}天，距截止日期还有{days_remaining}天",
            "priority": NotificationPriority.HIGH,
            "source_type": "ecn",
            "source_id": ecn_id,
            "link_url": f"/ecns?ecnId={ecn_id}",
        }
    )


# 向后兼容：保持原有函数接口，但内部使用统一NotificationService


def notify_approval_assigned(db, ecn_id: int, ecn_number: str, submitter_name: str):
    """通知审批分配（保持向后兼容）"""
    service = notification_service(db)
    return service.send_approval_pending(
        recipient_id=submitter_name,
        approval_id=ecn_id,
        title=f"ECN审批：{ecn_number}",
        submitter_name=submitter_name,
    )


def notify_approval_result(
    db, ecn_id: int, ecn_number: str, title: str, approved: bool, comment: str
):
    """通知审批结果（保持向后兼容）"""
    from app.models.ecn import Ecn

    service = notification_service(db)
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        return {"success": False}

    result = service.send_approval_result(
        recipient_id=ecn.applicant_id,
        approval_id=ecn_id,
        title=title,
        approved=approved,
        comment=comment,
    )
    return result.get("success", False)


# 导出原有的通知函数（保持向后兼容）
from .approval_notifications import (
    notify_approval_assigned as notify_approval_assigned_legacy,
    notify_approval_result as notify_approval_result_legacy,
)
from .evaluation_notifications import (
    notify_evaluation_assigned as notify_evaluation_assigned_legacy,
    notify_evaluation_completed as notify_evaluation_completed_legacy,
)
from .task_notifications import (
    notify_task_assigned as notify_task_assigned_legacy,
    notify_task_completed as notify_task_completed_legacy,
)

notify_approval_assigned = notify_approval_assigned_legacy
notify_approval_result = notify_approval_result_legacy
notify_evaluation_assigned = notify_evaluation_assigned_legacy
notify_evaluation_completed = notify_evaluation_completed_legacy
notify_task_assigned = notify_task_assigned_legacy
notify_task_completed = notify_task_completed_legacy

__all__ = [
    # 基础函数
    "create_ecn_notification",
    "find_users_by_department",
    "find_users_by_role",
    "find_department_manager",
    "check_all_evaluations_completed",
    # 使用统一服务的快捷函数
    "notify_ecn_submitted",
    "notify_overdue_alert",
    # 向后兼容：原有函数
    "notify_approval_assigned",
    "notify_approval_result",
    "notify_evaluation_assigned",
    "notify_evaluation_completed",
    "notify_task_assigned",
    "notify_task_completed",
    # ECN通知
    "notify_ecn_submitted",
    "notify_overdue_alert",
]
