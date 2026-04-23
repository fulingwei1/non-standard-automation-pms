# -*- coding: utf-8 -*-
"""notification_dispatcher 深度单测"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.alert import AlertNotification
from app.models.notification import Notification
from app.models.user import User
from app.services.notification.channels.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.notification_dispatcher import NotificationDispatcher


@pytest.fixture
def db_session():
    db = Mock()
    query = Mock()
    query.filter.return_value = query
    query.first.return_value = None
    db.query.return_value = query
    db.flush = Mock()
    db.add = Mock()
    return db


@pytest.fixture
def unified_service():
    svc = Mock()
    svc.send_notification.return_value = {"success": True}
    return svc


@pytest.fixture
def dispatcher(db_session, unified_service):
    with patch(
        "app.services.notification.notification_dispatcher.get_notification_service",
        return_value=unified_service,
    ):
        return NotificationDispatcher(db_session)


@pytest.fixture
def user():
    return SimpleNamespace(
        id=7,
        username="testuser",
        email="test@example.com",
        phone="13800138000",
        is_active=True,
    )


@pytest.fixture
def alert():
    return SimpleNamespace(
        id=1,
        alert_no="ALT-001",
        alert_level="WARNING",
        alert_title="Alert title",
        alert_content="Alert content",
        target_type="PROJECT",
        target_name="Project A",
        title="Fallback title",
        description="Fallback description",
        rule=None,
    )


@pytest.fixture
def notification(user):
    return SimpleNamespace(
        id=11,
        alert_id=1,
        notify_channel="EMAIL",
        notify_target=user.email,
        notify_user_id=user.id,
        notify_title="Notify title",
        notify_content="Notify content",
        status="PENDING",
        retry_count=0,
        next_retry_at=None,
        sent_at=None,
        error_message=None,
    )


def test_create_system_notification_adds_record(dispatcher, db_session):
    result = dispatcher.create_system_notification(
        recipient_id=7,
        notification_type="ALERT",
        title="t",
        content="c",
        source_type="alert",
        source_id=1,
        link_url="/alerts/1",
        priority="HIGH",
        extra_data={"a": 1},
    )

    assert isinstance(result, Notification)
    assert result.user_id == 7
    assert result.notification_type == "ALERT"
    assert result.title == "t"
    assert result.content == "c"
    db_session.add.assert_called_once_with(result)


def test_send_notification_request_forwards_to_unified_service(dispatcher, unified_service):
    request = NotificationRequest(
        recipient_id=7,
        notification_type="ALERT",
        category="alert",
        title="title",
        content="content",
    )

    dispatcher.send_notification_request(request)

    unified_service.send_notification.assert_called_once_with(request)


def test_resolve_recipients_by_ids_filters_invalid_ids(dispatcher, db_session, user):
    user_query = Mock()
    user_query.filter.return_value = user_query
    user_query.all.return_value = [user]

    settings = SimpleNamespace(user_id=user.id)
    settings_query = Mock()
    settings_query.filter.return_value = settings_query
    settings_query.all.return_value = [settings]

    def query_side_effect(model):
        if model is User:
            return user_query
        return settings_query

    db_session.query.side_effect = query_side_effect

    result = dispatcher._resolve_recipients_by_ids([user.id, None, "x", user.id])

    assert result == {user.id: {"user": user, "settings": settings}}


def test_resolve_recipients_by_ids_empty_returns_empty(dispatcher):
    assert dispatcher._resolve_recipients_by_ids([]) == {}
    assert dispatcher._resolve_recipients_by_ids([None, "x"]) == {}


def test_resolve_recipients_by_ids_no_users_returns_empty(dispatcher, db_session):
    user_query = Mock()
    user_query.filter.return_value = user_query
    user_query.all.return_value = []
    db_session.query.return_value = user_query

    assert dispatcher._resolve_recipients_by_ids([7]) == {}


def test_channel_and_priority_mapping(dispatcher):
    assert dispatcher._map_channel_to_unified("SYSTEM") == NotificationChannel.SYSTEM
    assert dispatcher._map_channel_to_unified("EMAIL") == NotificationChannel.EMAIL
    assert dispatcher._map_channel_to_unified("WECHAT") == NotificationChannel.WECHAT
    assert dispatcher._map_channel_to_unified("SMS") == NotificationChannel.SMS
    assert dispatcher._map_channel_to_unified("WEBHOOK") == NotificationChannel.WEBHOOK
    assert dispatcher._map_channel_to_unified("UNKNOWN") == NotificationChannel.SYSTEM

    assert dispatcher._map_alert_level_to_priority("URGENT") == NotificationPriority.URGENT
    assert dispatcher._map_alert_level_to_priority("CRITICAL") == NotificationPriority.URGENT
    assert dispatcher._map_alert_level_to_priority("WARNING") == NotificationPriority.HIGH
    assert dispatcher._map_alert_level_to_priority("INFO") == NotificationPriority.NORMAL
    assert dispatcher._map_alert_level_to_priority("") == NotificationPriority.NORMAL


def test_resolve_recipient_id_prefers_notification_then_user(dispatcher, notification, user):
    assert dispatcher._resolve_recipient_id(notification, None) == user.id

    notification.notify_user_id = None
    assert dispatcher._resolve_recipient_id(notification, user) == user.id

    with pytest.raises(ValueError):
        dispatcher._resolve_recipient_id(notification, None)


def test_build_notification_request_uses_fallback_fields(dispatcher, alert, notification, user):
    notification.notify_title = None
    notification.notify_content = None

    request = dispatcher.build_notification_request(notification, alert, user, force_send=True)

    assert request.recipient_id == user.id
    assert request.notification_type == "ALERT"
    assert request.category == "alert"
    assert request.title == alert.alert_title
    assert request.content == alert.alert_content
    assert request.priority == NotificationPriority.HIGH
    assert request.channels == [NotificationChannel.EMAIL]
    assert request.link_url == "/alerts/1"
    assert request.extra_data["alert_no"] == "ALT-001"
    assert request.force_send is True


def test_dispatch_quiet_hours_marks_pending(dispatcher, db_session, notification, alert, user):
    settings = SimpleNamespace()
    db_session.query.return_value.filter.return_value.first.return_value = settings

    with (
        patch("app.services.notification.notification_dispatcher.is_quiet_hours", return_value=True),
        patch(
            "app.services.notification.notification_dispatcher.next_quiet_resume",
            return_value=datetime(2026, 4, 11, 9, 0, 0),
        ),
    ):
        result = dispatcher.dispatch(notification, alert, user)

    assert result is True
    assert notification.status == "PENDING"
    assert notification.error_message == "Delayed due to quiet hours"
    assert notification.next_retry_at == datetime(2026, 4, 11, 9, 0, 0)


def test_dispatch_force_send_overrides_quiet_hours(dispatcher, notification, alert):
    request = NotificationRequest(
        recipient_id=7,
        notification_type="ALERT",
        category="alert",
        title="t",
        content="c",
        force_send=False,
    )

    with patch("app.services.notification.notification_dispatcher.is_quiet_hours", return_value=True):
        result = dispatcher.dispatch(notification, alert, None, request=request, force_send=True)

    assert result is True
    assert request.force_send is True
    assert notification.status == "SENT"


def test_dispatch_failed_result_updates_retry(dispatcher, unified_service, notification, alert, user):
    unified_service.send_notification.return_value = {"success": False, "message": "boom"}

    with patch("app.services.notification.notification_dispatcher.record_notification_failure") as mock_metric:
        result = dispatcher.dispatch(notification, alert, user)

    assert result is False
    assert notification.status == "FAILED"
    assert notification.error_message == "boom"
    assert notification.retry_count == 1
    assert notification.next_retry_at is not None
    mock_metric.assert_called_once_with("EMAIL")


def test_dispatch_exception_updates_retry(dispatcher, unified_service, notification, alert, user):
    unified_service.send_notification.side_effect = RuntimeError("send exploded")

    with patch("app.services.notification.notification_dispatcher.record_notification_failure") as mock_metric:
        result = dispatcher.dispatch(notification, alert, user)

    assert result is False
    assert notification.status == "FAILED"
    assert notification.error_message == "send exploded"
    assert notification.retry_count == 1
    assert notification.next_retry_at is not None
    mock_metric.assert_called_once_with("EMAIL")


def test_dispatch_alert_notifications_returns_zero_when_no_recipients(dispatcher, alert):
    with patch(
        "app.services.notification.notification_dispatcher.resolve_recipients",
        return_value={},
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 0, "queued": 0, "sent": 0, "failed": 0}


def test_dispatch_alert_notifications_handles_resolve_recipients_error(dispatcher, alert):
    with patch(
        "app.services.notification.notification_dispatcher.resolve_recipients",
        side_effect=RuntimeError("recipient lookup failed"),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 0, "queued": 0, "sent": 0, "failed": 0}


def test_dispatch_alert_notifications_queues_notifications(dispatcher, db_session, alert, user):
    recipients = {user.id: {"user": user, "settings": None}}
    db_session.query.return_value.filter.return_value.first.return_value = None

    with (
        patch(
            "app.services.notification.notification_dispatcher.resolve_recipients",
            return_value=recipients,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channels",
            return_value=["EMAIL", "SYSTEM"],
        ),
        patch(
            "app.services.notification.notification_dispatcher.channel_allowed",
            return_value=True,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            side_effect=[user.email, str(user.id)],
        ),
        patch(
            "app.services.notification.notification_queue.enqueue_notification",
            return_value=True,
        ),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 2, "queued": 2, "sent": 0, "failed": 0}
    assert db_session.add.call_count == 2
    db_session.flush.assert_called_once()


def test_dispatch_alert_notifications_falls_back_to_direct_dispatch(dispatcher, alert, user):
    recipients = {user.id: {"user": user, "settings": None}}

    with (
        patch.object(dispatcher, "_resolve_recipients_by_ids", return_value=recipients),
        patch(
            "app.services.notification.notification_dispatcher.channel_allowed",
            side_effect=lambda channel, settings: channel == "EMAIL",
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            side_effect=lambda channel, current_user: current_user.email if channel == "EMAIL" else None,
        ),
        patch(
            "app.services.notification.notification_queue.enqueue_notification",
            return_value=False,
        ),
        patch.object(dispatcher, "dispatch", return_value=True) as mock_dispatch,
    ):
        result = dispatcher.dispatch_alert_notifications(
            alert,
            user_ids=[user.id],
            channels=["EMAIL", "SMS"],
            title="Custom title",
            content="Custom content",
            force_send=True,
        )

    assert result == {"created": 1, "queued": 0, "sent": 1, "failed": 0}
    mock_dispatch.assert_called_once()
    args, kwargs = mock_dispatch.call_args
    created_notification = args[0]
    assert isinstance(created_notification, AlertNotification)
    assert created_notification.notify_title == "Custom title"
    assert created_notification.notify_content == "Custom content"
    assert kwargs["force_send"] is True


def test_dispatch_alert_notifications_handles_channel_resolution_fallbacks(dispatcher, alert, user):
    recipients = {
        user.id: {"user": user, "settings": None},
        99: {"user": None, "settings": None},
    }

    with (
        patch(
            "app.services.notification.notification_dispatcher.resolve_recipients",
            return_value=recipients,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channels",
            side_effect=RuntimeError("channels failed"),
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            return_value=None,
        ),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 0, "queued": 0, "sent": 0, "failed": 0}


def test_dispatch_alert_notifications_empty_channel_list_defaults_to_system(dispatcher, alert, user):
    recipients = {user.id: {"user": user, "settings": None}}

    with (
        patch(
            "app.services.notification.notification_dispatcher.resolve_recipients",
            return_value=recipients,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channels",
            return_value=[],
        ),
        patch(
            "app.services.notification.notification_dispatcher.channel_allowed",
            return_value=True,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            return_value=str(user.id),
        ),
        patch(
            "app.services.notification.notification_queue.enqueue_notification",
            return_value=True,
        ),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 1, "queued": 1, "sent": 0, "failed": 0}


def test_dispatch_alert_notifications_skips_disallowed_channel(dispatcher, alert, user):
    recipients = {user.id: {"user": user, "settings": SimpleNamespace()}}

    with (
        patch(
            "app.services.notification.notification_dispatcher.resolve_recipients",
            return_value=recipients,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channels",
            return_value=["EMAIL"],
        ),
        patch(
            "app.services.notification.notification_dispatcher.channel_allowed",
            return_value=False,
        ),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 0, "queued": 0, "sent": 0, "failed": 0}


def test_dispatch_alert_notifications_counts_failed_delivery(dispatcher, alert, user):
    recipients = {user.id: {"user": user, "settings": None}}

    with (
        patch.object(dispatcher, "_resolve_recipients_by_ids", return_value=recipients),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            return_value=user.email,
        ),
        patch(
            "app.services.notification.notification_queue.enqueue_notification",
            return_value=False,
        ),
        patch.object(dispatcher, "dispatch", return_value=False),
    ):
        result = dispatcher.dispatch_alert_notifications(
            alert,
            user_ids=[user.id],
            channels=["EMAIL"],
            force_send=True,
        )

    assert result == {"created": 1, "queued": 0, "sent": 0, "failed": 1}


def test_dispatch_alert_notifications_skips_existing_notifications(dispatcher, db_session, alert, user):
    recipients = {user.id: {"user": user, "settings": None}}
    existing = object()
    db_session.query.return_value.filter.return_value.first.return_value = existing

    with (
        patch(
            "app.services.notification.notification_dispatcher.resolve_recipients",
            return_value=recipients,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channels",
            return_value=["SYSTEM"],
        ),
        patch(
            "app.services.notification.notification_dispatcher.channel_allowed",
            return_value=True,
        ),
        patch(
            "app.services.notification.notification_dispatcher.resolve_channel_target",
            return_value=str(user.id),
        ),
    ):
        result = dispatcher.dispatch_alert_notifications(alert)

    assert result == {"created": 0, "queued": 0, "sent": 0, "failed": 0}
