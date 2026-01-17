# -*- coding: utf-8 -*-
"""
预警自动升级定时任务

实现预警超时未处理时的自动升级机制
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.base import get_db_session
from app.models.enums import AlertLevelEnum, AlertStatusEnum
from app.services.alert_rule_engine import AlertRuleEngine
from app.services.notification_service import AlertNotificationService


def check_alert_timeout_escalation():
    """
    预警超时自动升级服务
    每小时执行一次，检查超时未处理的预警并自动升级

    Returns:
        dict: 执行结果统计
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        with get_db_session() as db:
            engine = AlertRuleEngine(db)
            notification_service = AlertNotificationService(db)
            now = datetime.now()
            escalated_count = 0

            # 查询待处理或已确认的预警
            pending_alerts = db.query(AlertRecord).filter(
                AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED']),
                AlertRecord.is_escalated == False  # 未升级过的预警
            ).all()

            for alert in pending_alerts:
                # 计算预警持续时间
                if alert.triggered_at:
                    duration = now - alert.triggered_at
                elif alert.created_at:
                    duration = now - alert.created_at
                else:
                    continue

                # 获取响应时限（从规则配置或使用默认值）
                timeout_hours = engine.RESPONSE_TIMEOUT.get(alert.alert_level, 8)

                # 如果规则有配置响应时限，使用规则配置
                if alert.rule:
                    # 可以从规则配置中读取响应时限（如果规则表有该字段）
                    # 这里暂时使用默认值
                    pass

                # 检查是否超时
                if duration >= timedelta(hours=timeout_hours):
                    # 确定新的预警级别
                    new_level = _determine_escalated_level(alert.alert_level)

                    if new_level and engine.level_priority(new_level) > engine.level_priority(alert.alert_level):
                        # 升级预警
                        old_level = alert.alert_level
                        alert.alert_level = new_level
                        alert.is_escalated = True
                        alert.escalated_at = now

                        # 更新预警内容
                        alert.alert_title = f'[已升级] {alert.alert_title}'
                        alert.alert_content = (
                            f'{alert.alert_content}\n\n'
                            f'【自动升级】\n'
                            f'预警已超时 {duration.total_seconds() / 3600:.1f} 小时未处理，'
                            f'级别从 {old_level} 自动提升至 {new_level}'
                        )

                        db.add(alert)
                        db.flush()

                        # 发送升级通知
                        try:
                            notification_service.send_alert_notification(
                                alert=alert,
                                force_send=True  # 升级通知强制发送
                            )
                        except Exception as e:
                            logger.error(f"升级通知发送失败 (预警 {alert.alert_no}): {e}")

                        escalated_count += 1
                        logger.info(
                            f"预警自动升级: {alert.alert_no} "
                            f"({old_level} → {new_level}, 超时 {duration.total_seconds() / 3600:.1f} 小时)"
                        )

            db.commit()

            if escalated_count > 0:
                logger.info(
                    f"预警超时升级服务完成: 检查 {len(pending_alerts)} 个预警, 升级 {escalated_count} 个"
                )

            return {
                'checked_count': len(pending_alerts),
                'escalated_count': escalated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 预警超时升级服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def _determine_escalated_level(current_level: str) -> Optional[str]:
    """
    根据当前级别确定升级后的级别

    Args:
        current_level: 当前预警级别

    Returns:
        str: 升级后的级别，如果无法升级则返回 None
    """
    level_map = {
        AlertLevelEnum.INFO.value: AlertLevelEnum.WARNING.value,
        AlertLevelEnum.WARNING.value: AlertLevelEnum.CRITICAL.value,
        AlertLevelEnum.CRITICAL.value: AlertLevelEnum.URGENT.value,
        AlertLevelEnum.URGENT.value: None,  # URGENT 已经是最高级别
    }
    return level_map.get(current_level)
