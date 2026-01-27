# -*- coding: utf-8 -*-
"""
审批通知服务模块统一导出
模块结构：
- base.py                  # 基础类
- basic_notifications.py   # 基础通知（待审批、通过、驳回、抄送）
- reminder_notifications.py # 提醒通知（超时、催办）
- flow_notifications.py    # 流程变更通知（撤回、转审、代理、加签）
- comment_notifications.py   # 评论通知
- utils.py                 # 工具函数（去重、用户偏好）
- send_notification.py     # 发送通知（统一入口、站内通知保存）

向后兼容：所有原有函数接口保持不变
"""

from sqlalchemy.orm import Session

from .base import ApprovalNotifyServiceBase
from .basic_notifications import BasicNotificationsMixin
from .batch import BatchNotificationMixin
from .comment_notifications import CommentNotificationsMixin
from .external_channels import ExternalChannelsMixin
from .flow_notifications import FlowNotificationsMixin
from .reminder_notifications import ReminderNotificationsMixin
from .send_notification import SendNotificationMixin
from .utils import NotificationUtilsMixin

# 导入统一通知服务（已启用）
from app.services.unified_notification_service import (
    get_notification_service,
    NotificationService,
)


class ApprovalNotifyService(
    ApprovalNotifyServiceBase,
    NotificationUtilsMixin,
    BasicNotificationsMixin,
    ReminderNotificationsMixin,
    FlowNotificationsMixin,
    CommentNotificationsMixin,
    ExternalChannelsMixin,
    BatchNotificationMixin,
    SendNotificationMixin,
):
    """审批通知服务（组合所有功能模块）
    
    现在使用统一通知服务（unified_notification_service）进行所有通知发送。
    统一服务提供：
    - 自动去重
    - 用户偏好管理
    - 免打扰时间
    - 多渠道支持
    """

    def __init__(self, db: Session):
        ApprovalNotifyServiceBase.__init__(self, db)
        # 统一通知服务由 SendNotificationMixin 管理
        self._unified_service = None

    def get_unified_service(self) -> NotificationService:
        """获取统一通知服务单例（向后兼容方法）"""
        if self._unified_service is None:
            self._unified_service = get_notification_service(self.db)
        return self._unified_service


__all__ = ["ApprovalNotifyService"]
