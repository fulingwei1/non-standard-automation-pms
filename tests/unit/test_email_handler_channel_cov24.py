# -*- coding: utf-8 -*-
"""第二十四批 - channel_handlers/email_handler 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.channel_handlers.email_handler")

from app.services.channel_handlers.email_handler import EmailChannelHandler


def _make_channel_handler(email_enabled=True):
    db = MagicMock()
    with patch("app.services.channel_handlers.email_handler.settings") as ms:
        ms.EMAIL_ENABLED = email_enabled
        handler = EmailChannelHandler(db=db, channel="email")
    return handler, db


class TestEmailChannelHandlerIsEnabled:
    @patch("app.services.channel_handlers.email_handler.settings")
    def test_enabled_when_setting_true(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")
        assert handler.is_enabled() is True

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_disabled_when_setting_false(self, mock_settings):
        mock_settings.EMAIL_ENABLED = False
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")
        assert handler.is_enabled() is False


class TestEmailChannelHandlerSend:
    @patch("app.services.channel_handlers.email_handler.settings")
    def test_returns_failure_when_disabled(self, mock_settings):
        mock_settings.EMAIL_ENABLED = False
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")

        request = MagicMock()
        result = handler.send(request)
        assert result.success is False
        assert "未启用" in result.error_message

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_returns_failure_when_no_email(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")

        user = MagicMock()
        user.email = None
        db.query.return_value.filter.return_value.first.return_value = user

        request = MagicMock()
        request.recipient_id = 1
        result = handler.send(request)
        assert result.success is False
        assert "邮箱" in result.error_message

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_returns_success_with_valid_email(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")

        user = MagicMock()
        user.email = "user@company.com"
        db.query.return_value.filter.return_value.first.return_value = user

        request = MagicMock()
        request.recipient_id = 1
        request.title = "测试通知"
        result = handler.send(request)
        assert result.success is True

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_returns_failure_when_user_not_found(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailChannelHandler(db=db, channel="email")

        db.query.return_value.filter.return_value.first.return_value = None

        request = MagicMock()
        request.recipient_id = 999
        result = handler.send(request)
        assert result.success is False
