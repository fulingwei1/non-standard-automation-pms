# -*- coding: utf-8 -*-
"""第二十六批 - notification_utils 单元测试"""

import pytest
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock

pytest.importorskip("app.services.notification_utils")

from app.services.notification_utils import (
    get_alert_icon_url,
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    parse_time_str,
    is_quiet_hours,
    next_quiet_resume,
)


class TestGetAlertIconUrl:
    def test_urgent_returns_alarm_url(self):
        url = get_alert_icon_url("URGENT")
        assert "alarm" in url or "icons8" in url

    def test_warning_returns_warning_url(self):
        url = get_alert_icon_url("WARNING")
        assert "warning" in url or "icons8" in url

    def test_info_returns_info_url(self):
        url = get_alert_icon_url("INFO")
        assert "info" in url or "icons8" in url

    def test_critical_returns_high_priority_url(self):
        url = get_alert_icon_url("CRITICAL")
        assert "icons8" in url

    def test_unknown_level_returns_info_url(self):
        url = get_alert_icon_url("UNKNOWN_LEVEL")
        assert "icons8" in url

    def test_lowercase_input_works(self):
        url = get_alert_icon_url("urgent")
        assert url == get_alert_icon_url("URGENT")

    def test_tips_level_works(self):
        url = get_alert_icon_url("TIPS")
        assert url is not None and url.startswith("http")


class TestResolveChannels:
    def test_returns_system_when_no_rule(self):
        alert = MagicMock()
        alert.rule = None
        result = resolve_channels(alert)
        assert result == ["SYSTEM"]

    def test_returns_system_when_no_channels(self):
        alert = MagicMock()
        alert.rule.notify_channels = []
        result = resolve_channels(alert)
        assert result == ["SYSTEM"]

    def test_uppercases_channels(self):
        alert = MagicMock()
        alert.rule.notify_channels = ["email", "sms"]
        result = resolve_channels(alert)
        assert "EMAIL" in result
        assert "SMS" in result

    def test_multiple_channels_returned(self):
        alert = MagicMock()
        alert.rule.notify_channels = ["SYSTEM", "EMAIL", "WECHAT"]
        result = resolve_channels(alert)
        assert len(result) == 3


class TestResolveRecipients:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_dict_keyed_by_user_id(self):
        alert = MagicMock()
        alert.project = MagicMock(pm_id=1)
        alert.handler_id = None
        alert.rule.notify_users = []
        user = MagicMock(id=1, is_active=True)
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = resolve_recipients(self.db, alert)
        assert isinstance(result, dict)

    def test_includes_handler_id(self):
        alert = MagicMock()
        alert.project = None
        alert.handler_id = 5
        alert.rule.notify_users = []
        user = MagicMock(id=5, is_active=True)
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = resolve_recipients(self.db, alert)
        assert 5 in result

    def test_fallback_to_user_1_when_no_ids(self):
        alert = MagicMock()
        alert.project = None
        alert.handler_id = None
        alert.rule.notify_users = []
        user = MagicMock(id=1, is_active=True)
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = resolve_recipients(self.db, alert)
        assert 1 in result


class TestResolveChannelTarget:
    def test_system_returns_str_user_id(self):
        user = MagicMock(id=42)
        result = resolve_channel_target("SYSTEM", user)
        assert result == "42"

    def test_email_returns_email(self):
        user = MagicMock(email="test@example.com")
        result = resolve_channel_target("EMAIL", user)
        assert result == "test@example.com"

    def test_sms_returns_phone(self):
        user = MagicMock(phone="13900000000")
        result = resolve_channel_target("SMS", user)
        assert result == "13900000000"

    def test_wechat_returns_username(self):
        user = MagicMock(username="wechat_user", phone="139")
        result = resolve_channel_target("WECHAT", user)
        assert result == "wechat_user"

    def test_returns_none_when_user_is_none(self):
        result = resolve_channel_target("EMAIL", None)
        assert result is None

    def test_unknown_channel_returns_none(self):
        user = MagicMock()
        result = resolve_channel_target("TELEGRAM", user)
        assert result is None


class TestChannelAllowed:
    def test_no_settings_always_allowed(self):
        assert channel_allowed("EMAIL", None) is True
        assert channel_allowed("SYSTEM", None) is True

    def test_system_channel_respects_setting(self):
        settings = MagicMock(system_enabled=True)
        assert channel_allowed("SYSTEM", settings) is True
        settings.system_enabled = False
        assert channel_allowed("SYSTEM", settings) is False

    def test_email_channel_respects_setting(self):
        settings = MagicMock(email_enabled=False)
        assert channel_allowed("EMAIL", settings) is False

    def test_sms_channel_respects_setting(self):
        settings = MagicMock(sms_enabled=True)
        assert channel_allowed("SMS", settings) is True

    def test_wechat_channel_respects_setting(self):
        settings = MagicMock(wechat_enabled=False)
        assert channel_allowed("WECHAT", settings) is False

    def test_unknown_channel_allowed_by_default(self):
        settings = MagicMock()
        result = channel_allowed("UNKNOWN", settings)
        assert result is True


class TestParseTimeStr:
    def test_parses_valid_time(self):
        t = parse_time_str("08:30")
        assert t == time(8, 30)

    def test_parses_midnight(self):
        t = parse_time_str("00:00")
        assert t == time(0, 0)

    def test_parses_end_of_day(self):
        t = parse_time_str("23:59")
        assert t == time(23, 59)

    def test_returns_none_for_none(self):
        assert parse_time_str(None) is None

    def test_returns_none_for_empty_string(self):
        assert parse_time_str("") is None

    def test_returns_none_for_invalid_format(self):
        assert parse_time_str("not-a-time") is None


class TestIsQuietHours:
    def test_no_settings_returns_false(self):
        result = is_quiet_hours(None, datetime.now())
        assert result is False

    def test_quiet_hours_same_day(self):
        settings = MagicMock(quiet_hours_start="22:00", quiet_hours_end="23:59")
        dt = datetime.now().replace(hour=23, minute=0)
        assert is_quiet_hours(settings, dt) is True

    def test_not_quiet_outside_hours(self):
        settings = MagicMock(quiet_hours_start="22:00", quiet_hours_end="23:59")
        dt = datetime.now().replace(hour=10, minute=0)
        assert is_quiet_hours(settings, dt) is False

    def test_no_quiet_times_returns_false(self):
        settings = MagicMock(quiet_hours_start=None, quiet_hours_end=None)
        assert is_quiet_hours(settings, datetime.now()) is False

    def test_overnight_quiet_hours(self):
        settings = MagicMock(quiet_hours_start="23:00", quiet_hours_end="07:00")
        dt = datetime.now().replace(hour=2, minute=0)
        assert is_quiet_hours(settings, dt) is True


class TestNextQuietResume:
    def test_returns_future_resume_time(self):
        settings = MagicMock(quiet_hours_end="08:00")
        current = datetime.now().replace(hour=23, minute=0)
        resume = next_quiet_resume(settings, current)
        assert resume > current

    def test_adds_day_when_resume_in_past(self):
        settings = MagicMock(quiet_hours_end="07:00")
        current = datetime.now().replace(hour=10, minute=0)
        resume = next_quiet_resume(settings, current)
        assert resume > current

    def test_fallback_when_no_end_time(self):
        settings = MagicMock(quiet_hours_end=None)
        current = datetime.now()
        resume = next_quiet_resume(settings, current)
        # Should return something ~30 minutes in the future
        assert resume > current
        assert resume <= current + timedelta(minutes=31)
