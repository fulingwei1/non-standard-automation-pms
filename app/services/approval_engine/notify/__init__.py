# -*- coding: utf-8 -*-
"""
审批通知服务模块统一导出

模块结构:
 ├── base.py                  # 基础类
 ├── basic_notifications.py   # 基础通知（待审批、通过、驳回、抄送）
 ├── reminder_notifications.py # 提醒通知（超时、催办）
 ├── flow_notifications.py    # 流程变更通知（撤回、转审、代理、加签）
 ├── comment_notifications.py # 评论通知
 ├── utils.py                 # 工具函数（去重、用户偏好）
 ├── send_notification.py     # 发送通知（统一入口、站内通知）
 ├── external_channels.py     # 外部渠道（邮件、企微）
 └── batch.py                 # 批量通知
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


class ApprovalNotifyService(
    ApprovalNotifyServiceBase,
    NotificationUtilsMixin,
    BasicNotificationsMixin,
    ReminderNotificationsMixin,
    FlowNotificationsMixin,
    CommentNotificationsMixin,
    SendNotificationMixin,
    ExternalChannelsMixin,
    BatchNotificationMixin,
):
    """审批通知服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        ApprovalNotifyServiceBase.__init__(self, db)


__all__ = ["ApprovalNotifyService"]
