# -*- coding: utf-8 -*-
"""
企业微信预警消息推送服务（Wrapper for unified NotificationService）

这是WeChatAlertService的wrapper层，将调用转发到新的统一NotificationService
"""

from sqlalchemy.orm import Session

from app.services.unified_notification_service import NotificationService


class WeChatAlertService:
    """企业微信预警消息推送服务（使用统一NotificationService）"""

    def __init__(self, db: Session):
        self.db = db
        self._unified_service = NotificationService(db)

    @classmethod
    def send_shortage_alert(
        cls, db: Session, shortage_detail: "ShortageDetail", alert_level: str = "L4"
    ) -> bool:
        """发送缺料预警（使用统一的NotificationService）"""
        unified_service = NotificationService(db)
        return unified_service.send_shortage_alert(db, shortage_detail, alert_level)

    @classmethod
    def batch_send_alerts(cls, db: Session, alert_level: str = None) -> dict:
        """批量发送缺料预警（向后兼容）"""
        unified_service = NotificationService(db)
        return unified_service.batch_send_alerts(db, alert_level)
