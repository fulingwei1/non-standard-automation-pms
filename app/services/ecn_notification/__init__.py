# -*- coding: utf-8 -*-
"""
ECN通知服务（使用统一NotificationDispatcher）
功能：ECN相关通知的创建和发送

向后兼容：保持原有的函数接口，并支持新接口参数。
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.models.ecn import Ecn

from .base import create_ecn_notification
from .utils import (
    check_all_evaluations_completed,
    find_department_manager,
    find_users_by_department,
    find_users_by_role,
)

# 导出通知函数（统一到 NotificationDispatcher）
from .approval_notifications import (
    notify_approval_assigned as _notify_approval_assigned,
    notify_approval_result as _notify_approval_result,
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
    notify_ecn_submitted as _notify_ecn_submitted,
    notify_overdue_alert as _notify_overdue_alert,
)


def notify_ecn_submitted(
    db: Session,
    ecn_or_id: Union[Ecn, int],
    ecn_number: Optional[str] = None,
    submitter_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    发送ECN提交通知（兼容新旧签名）

    - 新签名：notify_ecn_submitted(db, ecn)
    - 旧签名：notify_ecn_submitted(db, ecn_id, ecn_number, submitter_name)
    """
    if isinstance(ecn_or_id, Ecn):
        _notify_ecn_submitted(db, ecn_or_id)
        return {"success": True}

    ecn_id = int(ecn_or_id)
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        return {"success": False, "message": "ECN不存在"}

    _notify_ecn_submitted(db, ecn)
    return {"success": True}


def notify_overdue_alert(
    db: Session,
    alert_or_id: Union[Dict[str, Any], int],
    user_ids: Optional[List[int]] = None,
    days_overdue: Optional[int] = None,
    days_remaining: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    发送ECN逾期预警（兼容新旧签名）

    - 新签名：notify_overdue_alert(db, alert, user_ids)
    - 旧签名：notify_overdue_alert(db, ecn_id, ecn_number, days_overdue, days_remaining)
    """
    if isinstance(alert_or_id, dict):
        if not user_ids:
            return {"success": False, "message": "缺少接收人"}
        _notify_overdue_alert(db, alert_or_id, user_ids)
        return {"success": True}

    ecn_id = int(alert_or_id)
    ecn_number = user_ids if isinstance(user_ids, str) else None
    overdue_days_value = days_overdue or 0
    remaining_days_value = days_remaining or 0

    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn or not ecn.applicant_id:
        return {"success": False, "message": "ECN或申请人不存在"}

    alert = {
        "ecn_id": ecn_id,
        "ecn_no": ecn_number or ecn.ecn_no,
        "overdue_days": overdue_days_value,
        "message": f"ECN {ecn_number or ecn.ecn_no} 已逾期{overdue_days_value}天，距截止日期还有{remaining_days_value}天",
    }
    _notify_overdue_alert(db, alert, [ecn.applicant_id])
    return {"success": True}


def notify_approval_assigned(*args, **kwargs):
    """保持旧接口入口，内部委托到通知模块实现。"""
    return _notify_approval_assigned(*args, **kwargs)


def notify_approval_result(*args, **kwargs):
    """保持旧接口入口，内部委托到通知模块实现。"""
    return _notify_approval_result(*args, **kwargs)


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
