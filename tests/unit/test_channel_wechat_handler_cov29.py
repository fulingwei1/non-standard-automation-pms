# -*- coding: utf-8 -*-
"""第二十九批 - channel_handlers/wechat_handler.py 单元测试（WeChatChannelHandler）"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.channel_handlers.wechat_handler")

from app.services.channel_handlers.wechat_handler import WeChatChannelHandler
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationPriority,
    NotificationChannel,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_request(**kwargs):
    return NotificationRequest(
        recipient_id=kwargs.get("recipient_id", 1),
        notification_type=kwargs.get("notification_type", "ALERT_NOTIFICATION"),
        category=kwargs.get("category", "alert"),
        title=kwargs.get("title", "测试标题"),
        content=kwargs.get("content", "测试内容"),
        priority=kwargs.get("priority", NotificationPriority.NORMAL),
        channels=[NotificationChannel.WECHAT],
        wechat_template=kwargs.get("wechat_template", None),
    )


def _make_user(user_id=1, wechat_userid="wx_user_1"):
    u = MagicMock()
    u.id = user_id
    u.wechat_userid = wechat_userid
    return u


# ─── 测试：is_enabled ─────────────────────────────────────────────────────────

class TestWeChatChannelHandlerIsEnabled:
    """测试 is_enabled 方法"""

    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_enabled_when_setting_true(self, mock_settings):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        assert handler.is_enabled() is True

    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_disabled_when_setting_false(self, mock_settings):
        mock_settings.WECHAT_ENABLED = False
        db = _make_db()
        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        assert handler.is_enabled() is False


# ─── 测试：send ───────────────────────────────────────────────────────────────

class TestWeChatChannelHandlerSend:
    """测试 send 方法"""

    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_returns_failure_when_disabled(self, mock_settings):
        mock_settings.WECHAT_ENABLED = False
        db = _make_db()
        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request()
        result = handler.send(request)
        assert result.success is False
        assert "未启用" in result.error_message

    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_returns_failure_when_user_not_found(self, mock_settings):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request(recipient_id=999)
        result = handler.send(request)
        assert result.success is False
        assert "未绑定" in result.error_message

    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_returns_failure_when_user_has_no_wechat_id(self, mock_settings):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        user = _make_user(wechat_userid=None)
        db.query.return_value.filter.return_value.first.return_value = user
        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request()
        result = handler.send(request)
        assert result.success is False

    @patch("app.services.channel_handlers.wechat_handler.WeChatClient")
    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_sends_text_message_success(self, mock_settings, mock_client_cls):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        user = _make_user(wechat_userid="wx_abc")
        db.query.return_value.filter.return_value.first.return_value = user
        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client.last_sent_time = "2025-01-01T00:00:00"
        mock_client_cls.return_value = mock_client

        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request()
        result = handler.send(request)

        assert result.success is True
        mock_client.send_message.assert_called_once_with(["wx_abc"], {
            "msgtype": "text",
            "text": {"content": f"【{request.title}】\n{request.content}"},
        })

    @patch("app.services.channel_handlers.wechat_handler.WeChatClient")
    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_sends_template_card_when_wechat_template_present(self, mock_settings, mock_client_cls):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        user = _make_user(wechat_userid="wx_xyz")
        db.query.return_value.filter.return_value.first.return_value = user
        mock_client = MagicMock()
        mock_client.send_template_card.return_value = True
        mock_client.last_sent_time = "2025-01-01T00:00:00"
        mock_client_cls.return_value = mock_client

        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        template_card = {"card_type": "text_notice", "template_card": {"card_type": "text_notice"}}
        request = _make_request(wechat_template=template_card)
        result = handler.send(request)

        assert result.success is True
        mock_client.send_template_card.assert_called_once()

    @patch("app.services.channel_handlers.wechat_handler.WeChatClient")
    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_handles_exception_gracefully(self, mock_settings, mock_client_cls):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        user = _make_user(wechat_userid="wx_err")
        db.query.return_value.filter.return_value.first.return_value = user
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("网络异常")
        mock_client_cls.return_value = mock_client

        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request()
        result = handler.send(request)

        assert result.success is False
        assert "网络异常" in result.error_message

    @patch("app.services.channel_handlers.wechat_handler.WeChatClient")
    @patch("app.services.channel_handlers.wechat_handler.settings")
    def test_returns_failure_when_client_returns_false(self, mock_settings, mock_client_cls):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        user = _make_user(wechat_userid="wx_fail")
        db.query.return_value.filter.return_value.first.return_value = user
        mock_client = MagicMock()
        mock_client.send_message.return_value = False
        mock_client_cls.return_value = mock_client

        handler = WeChatChannelHandler(db=db, channel=NotificationChannel.WECHAT)
        request = _make_request()
        result = handler.send(request)

        assert result.success is False
        assert "发送失败" in result.error_message
