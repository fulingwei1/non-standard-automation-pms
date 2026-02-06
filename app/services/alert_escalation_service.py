# -*- coding: utf-8 -*-
"""
预警升级服务
S.10: 实现预警升级机制，自动升级超时未处理的预警
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


class AlertEscalationService:
    """预警升级服务"""

    # 预警级别升级路径
    ESCALATION_PATH = {
        'INFO': 'WARN',
        'WARN': 'HIGH',
        'HIGH': 'CRITICAL',
        'MEDIUM': 'HIGH',
        'LOW': 'MEDIUM',
    }

    # 各级别的超时时间（小时）
    ESCALATION_TIMEOUT = {
        'INFO': 48,
        'WARN': 24,
        'HIGH': 12,
        'CRITICAL': 6,
        'MEDIUM': 24,
        'LOW': 48,
    }

    def __init__(self, db: Session):
        self.db = db

    def check_and_escalate(self) -> Dict[str, Any]:
        """
        检查所有未处理的预警并进行升级

        Returns:
            Dict: {
                'checked': 检查的预警数量,
                'escalated': 升级的预警数量,
                'errors': 错误列表
            }
        """
        checked_count = 0
        escalated_count = 0
        errors = []

        try:
            # 查询所有待处理的预警
            pending_alerts = self.db.query(AlertRecord).filter(
                AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED']),
                AlertRecord.alert_level != 'CRITICAL'  # CRITICAL已是最高级别
            ).all()

            checked_count = len(pending_alerts)

            for alert in pending_alerts:
                try:
                    if self._should_escalate(alert):
                        self._escalate_alert(alert)
                        escalated_count += 1
                except Exception as e:
                    errors.append({
                        'alert_id': alert.id,
                        'error': str(e)
                    })
                    logger.warning(f"升级预警 {alert.id} 失败: {e}")

            self.db.commit()

        except Exception as e:
            logger.error(f"预警升级检查失败: {e}", exc_info=True)
            errors.append({'error': str(e)})

        return {
            'checked': checked_count,
            'escalated': escalated_count,
            'errors': errors
        }

    def _should_escalate(self, alert: AlertRecord) -> bool:
        """
        判断预警是否需要升级

        Args:
            alert: 预警记录

        Returns:
            bool: 是否需要升级
        """
        if not alert.triggered_at:
            return False

        current_level = alert.alert_level or 'MEDIUM'
        timeout_hours = self.ESCALATION_TIMEOUT.get(current_level, 24)
        timeout_threshold = datetime.now() - timedelta(hours=timeout_hours)

        return alert.triggered_at < timeout_threshold

    def _escalate_alert(self, alert: AlertRecord) -> None:
        """
        执行预警升级

        Args:
            alert: 预警记录
        """
        current_level = alert.alert_level or 'MEDIUM'
        new_level = self.ESCALATION_PATH.get(current_level)

        if not new_level:
            return

        old_level = alert.alert_level
        alert.alert_level = new_level

        # 添加升级记录到alert_data
        import json
        alert_data = json.loads(alert.alert_data) if alert.alert_data else {}
        if 'escalation_history' not in alert_data:
            alert_data['escalation_history'] = []
        alert_data['escalation_history'].append({
            'from_level': old_level,
            'to_level': new_level,
            'escalated_at': datetime.now().isoformat(),
            'reason': '超时自动升级'
        })
        alert.alert_data = json.dumps(alert_data, ensure_ascii=False)

        self.db.add(alert)

        # 创建升级通知
        self._send_escalation_notification(alert, old_level, new_level)

        logger.info(f"预警 {alert.alert_no} 已从 {old_level} 升级到 {new_level}")

    def _send_escalation_notification(
        self,
        alert: AlertRecord,
        old_level: str,
        new_level: str
    ) -> None:
        """
        发送预警升级通知

        Args:
            alert: 预警记录
            old_level: 原级别
            new_level: 新级别
        """
        try:
            notification = Notification(
                user_id=None,  # 发给系统管理员
                title=f'预警已升级: {alert.alert_title}',
                content=f'预警 "{alert.alert_title}" 因超时未处理，已从 {old_level} 升级至 {new_level}。\n'
                        f'预警内容: {alert.alert_content[:200]}...',
                notification_type='alert_escalation',
                priority='high' if new_level == 'CRITICAL' else 'normal',
                is_read=False,
                source_type='alert_record',
                source_id=alert.id
            )
            self.db.add(notification)

        except Exception as e:
            logger.error(f"发送升级通知失败: {e}")
