# -*- coding: utf-8 -*-
"""
UnifiedNotificationService (NotificationService) 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _get_user_settings: 获取用户设置
- _check_dedup: 检查重复通知
- _dedup_key: 生成去重key
- _update_dedup_cache: 更新去重缓存
- _check_quiet_hours: 检查免打扰时间
- _should_send_by_category: 根据分类检查
- _determine_channels: 确定通知渠道
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, time
from hashlib import md5

import pytest


class TestNotificationServiceInit:
    """测试 NotificationService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()

                            service = NotificationService(mock_db)

                            assert service.db == mock_db

    def test_initializes_handlers(self):
        """测试初始化通知处理器"""
        with patch('app.services.unified_notification_service.SystemChannelHandler') as mock_sys:
            with patch('app.services.unified_notification_service.EmailChannelHandler') as mock_email:
                with patch('app.services.unified_notification_service.WeChatChannelHandler') as mock_wechat:
                    with patch('app.services.unified_notification_service.SMSChannelHandler') as mock_sms:
                        with patch('app.services.unified_notification_service.WebhookChannelHandler') as mock_webhook:
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()

                            service = NotificationService(mock_db)

                            assert len(service._handlers) == 5


class TestGetUserSettings:
    """测试 _get_user_settings 方法"""

    def test_returns_user_settings(self):
        """测试返回用户设置"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            mock_settings = MagicMock()
                            mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

                            service = NotificationService(mock_db)
                            result = service._get_user_settings(1)

                            assert result == mock_settings

    def test_returns_none_when_no_settings(self):
        """测试没有设置时返回 None"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            mock_db.query.return_value.filter.return_value.first.return_value = None

                            service = NotificationService(mock_db)
                            result = service._get_user_settings(999)

                            assert result is None


class TestCheckDedup:
    """测试 _check_dedup 方法"""

    def test_returns_false_when_force_send(self):
        """测试强制发送时返回 False"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.force_send = True

                            result = service._check_dedup(mock_request)

                            assert result is False

    def test_returns_true_when_duplicate(self):
        """测试重复通知时返回 True"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.force_send = False
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            # 先添加到缓存
                            dedup_key = service._dedup_key(mock_request)
                            service._dedup_cache[dedup_key] = datetime.now()

                            result = service._check_dedup(mock_request)

                            assert result is True

    def test_returns_false_when_not_duplicate(self):
        """测试非重复通知时返回 False"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)
                            service._dedup_cache = {}  # 清空缓存

                            mock_request = MagicMock()
                            mock_request.force_send = False
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            result = service._check_dedup(mock_request)

                            assert result is False


class TestDedupKey:
    """测试 _dedup_key 方法"""

    def test_generates_consistent_key(self):
        """测试生成一致的 key"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            key1 = service._dedup_key(mock_request)
                            key2 = service._dedup_key(mock_request)

                            assert key1 == key2

    def test_generates_md5_hash(self):
        """测试生成 MD5 哈希"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            key = service._dedup_key(mock_request)

                            expected = md5("1:alert:project:100".encode()).hexdigest()
                            assert key == expected


class TestUpdateDedupCache:
    """测试 _update_dedup_cache 方法"""

    def test_updates_cache_when_not_force_send(self):
        """测试非强制发送时更新缓存"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)
                            service._dedup_cache = {}

                            mock_request = MagicMock()
                            mock_request.force_send = False
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            service._update_dedup_cache(mock_request)

                            dedup_key = service._dedup_key(mock_request)
                            assert dedup_key in service._dedup_cache

    def test_skips_update_when_force_send(self):
        """测试强制发送时跳过更新"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)
                            service._dedup_cache = {}

                            mock_request = MagicMock()
                            mock_request.force_send = True
                            mock_request.recipient_id = 1
                            mock_request.notification_type = "alert"
                            mock_request.source_type = "project"
                            mock_request.source_id = 100

                            service._update_dedup_cache(mock_request)

                            assert len(service._dedup_cache) == 0


class TestCheckQuietHours:
    """测试 _check_quiet_hours 方法"""

    def test_returns_false_when_no_settings(self):
        """测试没有设置时返回 False"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            result = service._check_quiet_hours(None)

                            assert result is False

    def test_returns_false_when_no_quiet_hours(self):
        """测试没有免打扰时间设置时返回 False"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_settings = MagicMock()
                            mock_settings.quiet_hours_start = None
                            mock_settings.quiet_hours_end = None

                            result = service._check_quiet_hours(mock_settings)

                            assert result is False


class TestShouldSendByCategory:
    """测试 _should_send_by_category 方法"""

    def test_returns_true_when_no_settings(self):
        """测试没有设置时返回 True"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.force_send = False
                            mock_request.category = "task"

                            result = service._should_send_by_category(mock_request, None)

                            assert result is True

    def test_returns_true_when_force_send(self):
        """测试强制发送时返回 True"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.force_send = True
                            mock_request.category = "task"

                            mock_settings = MagicMock()
                            mock_settings.task_notifications = False

                            result = service._should_send_by_category(mock_request, mock_settings)

                            assert result is True

    def test_checks_task_notifications(self):
        """测试检查任务通知设置"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.force_send = False
                            mock_request.category = "task"

                            mock_settings = MagicMock()
                            mock_settings.task_notifications = True

                            result = service._should_send_by_category(mock_request, mock_settings)

                            assert result is True


class TestDetermineChannels:
    """测试 _determine_channels 方法"""

    def test_uses_specified_channels(self):
        """测试使用指定的渠道"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService

                            mock_db = MagicMock()
                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.channels = ["EMAIL", "WECHAT"]
                            mock_request.recipient_id = 1

                            result = service._determine_channels(mock_request)

                            assert result == ["EMAIL", "WECHAT"]

    def test_defaults_to_system_channel(self):
        """测试默认使用系统渠道"""
        with patch('app.services.unified_notification_service.SystemChannelHandler'):
            with patch('app.services.unified_notification_service.EmailChannelHandler'):
                with patch('app.services.unified_notification_service.WeChatChannelHandler'):
                    with patch('app.services.unified_notification_service.SMSChannelHandler'):
                        with patch('app.services.unified_notification_service.WebhookChannelHandler'):
                            from app.services.unified_notification_service import NotificationService
                            from app.services.channel_handlers.base import NotificationChannel, NotificationPriority

                            mock_db = MagicMock()
                            mock_db.query.return_value.filter.return_value.first.return_value = None

                            service = NotificationService(mock_db)

                            mock_request = MagicMock()
                            mock_request.channels = None
                            mock_request.priority = NotificationPriority.NORMAL
                            mock_request.recipient_id = 1

                            result = service._determine_channels(mock_request)

                            assert NotificationChannel.SYSTEM in result
