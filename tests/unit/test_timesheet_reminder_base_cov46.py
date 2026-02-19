# -*- coding: utf-8 -*-
"""第四十六批 - 工时提醒基础服务单元测试"""
import pytest

pytest.importorskip("app.services.timesheet_reminder.base",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.timesheet_reminder.base import create_timesheet_notification


class TestCreateTimesheetNotification:
    def test_calls_dispatcher_create_system_notification(self):
        db = MagicMock()
        mock_notification = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = mock_notification

        with patch("app.services.timesheet_reminder.base.NotificationDispatcher",
                   return_value=mock_dispatcher):
            result = create_timesheet_notification(
                db=db,
                user_id=1,
                notification_type="FILL_REMINDER",
                title="请填写工时",
                content="您有未填写的工时"
            )

        mock_dispatcher.create_system_notification.assert_called_once()
        assert result is mock_notification

    def test_passes_correct_params(self):
        db = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = MagicMock()

        with patch("app.services.timesheet_reminder.base.NotificationDispatcher",
                   return_value=mock_dispatcher):
            create_timesheet_notification(
                db=db,
                user_id=42,
                notification_type="ANOMALY_ALERT",
                title="工时异常",
                content="检测到异常工时",
                source_type="timesheet",
                source_id=100,
                link_url="/timesheet/100",
                priority="HIGH",
                extra_data={"hours": 25}
            )

        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs["recipient_id"] == 42
        assert call_kwargs["notification_type"] == "ANOMALY_ALERT"
        assert call_kwargs["priority"] == "HIGH"

    def test_defaults_link_url_to_timesheet(self):
        db = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = MagicMock()

        with patch("app.services.timesheet_reminder.base.NotificationDispatcher",
                   return_value=mock_dispatcher):
            create_timesheet_notification(
                db=db,
                user_id=1,
                notification_type="TYPE",
                title="标题",
                content="内容",
                link_url=None
            )

        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs["link_url"] == "/timesheet"

    def test_defaults_extra_data_to_empty_dict(self):
        db = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = MagicMock()

        with patch("app.services.timesheet_reminder.base.NotificationDispatcher",
                   return_value=mock_dispatcher):
            create_timesheet_notification(
                db=db,
                user_id=1,
                notification_type="TYPE",
                title="标题",
                content="内容",
                extra_data=None
            )

        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs["extra_data"] == {}

    def test_dispatcher_initialized_with_db(self):
        db = MagicMock()
        with patch("app.services.timesheet_reminder.base.NotificationDispatcher") as MockDispatcher:
            MockDispatcher.return_value.create_system_notification.return_value = MagicMock()
            create_timesheet_notification(
                db=db, user_id=1, notification_type="T",
                title="T", content="C"
            )
        MockDispatcher.assert_called_once_with(db)
