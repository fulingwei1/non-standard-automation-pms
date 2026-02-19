# -*- coding: utf-8 -*-
"""
Tests for app/services/timesheet_reminder/base.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.timesheet_reminder.base import create_timesheet_notification
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


def test_create_notification_calls_dispatcher(mock_db):
    """应创建 NotificationDispatcher 并调用 create_system_notification"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        mock_dispatcher.create_system_notification.return_value = MagicMock()
        result = create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TIMESHEET_REMINDER",
            title="工时提醒",
            content="请填写工时",
        )
        MockDispatcher.assert_called_once_with(mock_db)
        mock_dispatcher.create_system_notification.assert_called_once()


def test_create_notification_default_link_url(mock_db):
    """默认 link_url 应为 /timesheet"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TYPE",
            title="T",
            content="C",
        )
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("link_url") == "/timesheet"


def test_create_notification_custom_link_url(mock_db):
    """自定义 link_url 时应使用自定义值"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TYPE",
            title="T",
            content="C",
            link_url="/custom/path",
        )
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("link_url") == "/custom/path"


def test_create_notification_passes_priority(mock_db):
    """优先级参数应传递给 dispatcher"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TYPE",
            title="T",
            content="C",
            priority="HIGH",
        )
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("priority") == "HIGH"


def test_create_notification_empty_extra_data(mock_db):
    """不传 extra_data 时应传空字典"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        create_timesheet_notification(
            db=mock_db,
            user_id=2,
            notification_type="TYPE",
            title="T",
            content="C",
        )
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("extra_data") == {}


def test_create_notification_source_type_default(mock_db):
    """默认 source_type 应为 timesheet"""
    with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TYPE",
            title="T",
            content="C",
        )
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("source_type") == "timesheet"
