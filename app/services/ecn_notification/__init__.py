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
    from app.services.channel_handlers.base import NotificationRequest
    
    service = notification_service(db)
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn or not ecn.applicant_id:
        return {"success": False, "message": "ECN或申请人不存在"}
    
    request = NotificationRequest(
        recipient_id=ecn.applicant_id,
        notification_type="ECN_OVERDUE",
        category="ecn",
        title="ECN逾期提醒",
        content=f"ECN {ecn_number} 已逾期{days_overdue}天，距截止日期还有{days_remaining}天",
        priority=NotificationPriority.HIGH,
        source_type="ecn",
        source_id=ecn_id,
        link_url=f"/ecns?ecnId={ecn_id}",
    )
    return service.send_notification(request)


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


# 导出通知函数（已迁移到统一服务）
from .approval_notifications import (
    notify_approval_assigned,
    notify_approval_result,
)
from .evaluation_notifications import (
    notify_evaluation_assigned,
    notify_evaluation_completed,
)
from .task_notifications import (
    notify_task_assigned,
    notify_task_completed,
)
from .ecn_notifications import (
    notify_ecn_submitted as notify_ecn_submitted_legacy,
    notify_overdue_alert as notify_overdue_alert_legacy,
)

__all__ = [
    # 基础函数（已迁移到统一服务，保留用于向后兼容）
    "create_ecn_notification",
    # 工具函数
    "find_users_by_department",
    "find_users_by_role",
    "find_department_manager",
    "check_all_evaluations_completed",
    # 通知函数（已迁移到统一服务）
    "notify_ecn_submitted",
    "notify_overdue_alert",
    "notify_approval_assigned",
    "notify_approval_result",
    "notify_evaluation_assigned",
    "notify_evaluation_completed",
    "notify_task_assigned",
    "notify_task_completed",
]
