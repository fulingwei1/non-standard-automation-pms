# -*- coding: utf-8 -*-
"""
审批通知服务 - 工具函数

提供通知去重、用户偏好检查等工具函数
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict

from app.models.notification import NotificationSettings

from .base import _notification_dedup_cache

logger = logging.getLogger(__name__)


class NotificationUtilsMixin:
    """通知工具函数 Mixin"""

    def _generate_dedup_key(self, notification: Dict) -> str:
        """生成通知去重的唯一键"""
        key_parts = [
            str(notification.get("type", "")),
            str(notification.get("receiver_id", "")),
            str(notification.get("instance_id", "")),
            str(notification.get("task_id", "")),
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_duplicate(self, dedup_key: str) -> bool:
        """检查是否为重复通知（基于用户偏好的去重窗口）

        通过解析 dedup_key 获取 recipient_id 和通知类型，
        然后查询用户偏好中的 dedup_window_hours 决定是否启用去重。
        - dedup_window_hours > 0：去重启用，在窗口内视为重复
        - dedup_window_hours == 0：去重禁用，始终不视为重复
        """
        global _notification_dedup_cache

        # 从 dedup_key 中解析 recipient_id 和通知类型
        # key 格式: "instance_id:node_id:task_id:type:recipient_id"
        parts = dedup_key.split(":")
        recipient_id = int(parts[-1]) if len(parts) >= 5 else 0
        notification_type = parts[-2] if len(parts) >= 5 else ""

        # 查询用户偏好，获取去重窗口配置
        prefs = self._check_user_preferences(recipient_id, notification_type)
        dedup_window_hours = prefs.get("dedup_window_hours", 0)

        # 去重窗口为 0 表示禁用去重，直接返回 False
        if dedup_window_hours <= 0:
            return False

        now = datetime.now()

        # 清理过期的缓存项（基于用户配置的去重窗口）
        expired_keys = [
            k for k, v in _notification_dedup_cache.items()
            if now - v > timedelta(hours=dedup_window_hours)
        ]
        for k in expired_keys:
            del _notification_dedup_cache[k]

        # 检查是否存在于缓存中
        if dedup_key in _notification_dedup_cache:
            # 缓存中已有该 key，视为重复
            return True

        # 添加到缓存，标记为已发送
        _notification_dedup_cache[dedup_key] = now
        return True

    def _check_user_preferences(self, user_id: int, notification_type: str) -> Dict[str, bool]:
        """
        检查用户通知偏好设置

        Returns:
            包含各渠道是否启用的字典
        """
        default_prefs = {
            "system_enabled": True,
            "email_enabled": False,
            "wechat_enabled": False,
            "sms_enabled": False,
        }

        try:
            settings = (
                self.db.query(NotificationSettings)
                .filter(NotificationSettings.user_id == user_id)
                .first()
            )

            if not settings:
                return default_prefs

            # 检查用户是否启用审批通知
            if not settings.approval_notifications:
                return {k: False for k in default_prefs}

            # 检查免打扰时间
            if settings.quiet_hours_start and settings.quiet_hours_end:
                now_time = datetime.now().strftime("%H:%M")
                if settings.quiet_hours_start <= now_time <= settings.quiet_hours_end:
                    # 免打扰时间内只发站内通知
                    return {
                        "system_enabled": settings.system_enabled,
                        "email_enabled": False,
                        "wechat_enabled": False,
                        "sms_enabled": False,
                    }

            return {
                "system_enabled": settings.system_enabled,
                "email_enabled": settings.email_enabled,
                "wechat_enabled": settings.wechat_enabled,
                "sms_enabled": settings.sms_enabled,
            }

        except Exception as e:
            logger.warning(f"获取用户通知偏好失败: {e}")
            return default_prefs
