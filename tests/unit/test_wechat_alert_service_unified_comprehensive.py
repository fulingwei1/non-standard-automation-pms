# -*- coding: utf-8 -*-
"""
WeChatAlertService (unified) 综合单元测试

测试覆盖:
- __init__: 初始化服务
- send_shortage_alert: 发送缺料预警
- batch_send_alerts: 批量发送预警
"""

from unittest.mock import MagicMock, patch

import pytest


class TestWeChatAlertServiceInit:
    """测试 WeChatAlertService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()

            service = WeChatAlertService(mock_db)

            assert service.db == mock_db
            mock_service.assert_called_once_with(mock_db)

    def test_creates_unified_service(self):
        """测试创建统一通知服务"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_service.return_value = mock_unified

            service = WeChatAlertService(mock_db)

            assert service._unified_service == mock_unified


class TestSendShortageAlert:
    """测试 send_shortage_alert 方法"""

    def test_delegates_to_unified_service(self):
        """测试委托给统一服务"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_unified.send_shortage_alert.return_value = True
            mock_service.return_value = mock_unified

            mock_shortage = MagicMock()

            result = WeChatAlertService.send_shortage_alert(
                mock_db,
                mock_shortage,
                alert_level="L3"
            )

            mock_unified.send_shortage_alert.assert_called_once_with(
                mock_db,
                mock_shortage,
                "L3"
            )
            assert result is True

    def test_uses_default_alert_level(self):
        """测试使用默认预警级别"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_unified.send_shortage_alert.return_value = True
            mock_service.return_value = mock_unified

            mock_shortage = MagicMock()

            result = WeChatAlertService.send_shortage_alert(
                mock_db,
                mock_shortage
            )

            mock_unified.send_shortage_alert.assert_called_once_with(
                mock_db,
                mock_shortage,
                "L4"
            )

    def test_returns_false_on_failure(self):
        """测试失败时返回False"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_unified.send_shortage_alert.return_value = False
            mock_service.return_value = mock_unified

            mock_shortage = MagicMock()

            result = WeChatAlertService.send_shortage_alert(
                mock_db,
                mock_shortage
            )

            assert result is False


class TestBatchSendAlerts:
    """测试 batch_send_alerts 方法"""

    def test_delegates_to_unified_service(self):
        """测试委托给统一服务"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_unified.batch_send_alerts.return_value = {"sent": 5, "failed": 0}
            mock_service.return_value = mock_unified

            result = WeChatAlertService.batch_send_alerts(mock_db, alert_level="L2")

            mock_unified.batch_send_alerts.assert_called_once_with(mock_db, "L2")
            assert result == {"sent": 5, "failed": 0}

    def test_passes_none_alert_level(self):
        """测试传递None预警级别"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            mock_unified.batch_send_alerts.return_value = {"sent": 10}
            mock_service.return_value = mock_unified

            result = WeChatAlertService.batch_send_alerts(mock_db)

            mock_unified.batch_send_alerts.assert_called_once_with(mock_db, None)

    def test_returns_result_dict(self):
        """测试返回结果字典"""
        with patch('app.services.wechat_alert_service_unified.NotificationService') as mock_service:
            from app.services.wechat_alert_service_unified import WeChatAlertService

            mock_db = MagicMock()
            mock_unified = MagicMock()
            expected_result = {
                "sent": 3,
                "failed": 1,
                "errors": ["error1"]
            }
            mock_unified.batch_send_alerts.return_value = expected_result
            mock_service.return_value = mock_unified

            result = WeChatAlertService.batch_send_alerts(mock_db)

            assert result == expected_result
