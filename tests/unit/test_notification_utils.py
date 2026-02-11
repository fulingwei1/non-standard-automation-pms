# -*- coding: utf-8 -*-
"""Tests for app.services.notification_utils"""

import unittest
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock

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


class TestGetAlertIconUrl(unittest.TestCase):

    def test_known_levels(self):
        self.assertIn("alarm", get_alert_icon_url("URGENT"))
        self.assertIn("high-priority", get_alert_icon_url("CRITICAL"))
        self.assertIn("warning", get_alert_icon_url("WARNING"))
        self.assertIn("info", get_alert_icon_url("INFO"))
        self.assertIn("light-bulb", get_alert_icon_url("TIPS"))

    def test_unknown_level_defaults_to_info(self):
        self.assertIn("info", get_alert_icon_url("UNKNOWN"))

    def test_case_insensitive(self):
        self.assertIn("alarm", get_alert_icon_url("urgent"))


class TestResolveChannels(unittest.TestCase):

    def test_with_rule_channels(self):
        alert = MagicMock()
        alert.rule.notify_channels = ["email", "wechat"]
        result = resolve_channels(alert)
        self.assertEqual(result, ["EMAIL", "WECHAT"])

    def test_no_rule(self):
        alert = MagicMock()
        alert.rule = None
        result = resolve_channels(alert)
        self.assertEqual(result, ["SYSTEM"])

    def test_empty_channels(self):
        alert = MagicMock()
        alert.rule.notify_channels = []
        result = resolve_channels(alert)
        self.assertEqual(result, ["SYSTEM"])


class TestResolveChannelTarget(unittest.TestCase):

    def test_system(self):
        user = MagicMock()
        user.id = 42
        self.assertEqual(resolve_channel_target("SYSTEM", user), "42")

    def test_email(self):
        user = MagicMock()
        user.email = "a@b.com"
        self.assertEqual(resolve_channel_target("EMAIL", user), "a@b.com")

    def test_sms(self):
        user = MagicMock()
        user.phone = "123"
        self.assertEqual(resolve_channel_target("SMS", user), "123")

    def test_no_user(self):
        self.assertIsNone(resolve_channel_target("SYSTEM", None))


class TestChannelAllowed(unittest.TestCase):

    def test_no_settings_allows_all(self):
        self.assertTrue(channel_allowed("EMAIL", None))

    def test_email_disabled(self):
        settings = MagicMock()
        settings.email_enabled = False
        self.assertFalse(channel_allowed("EMAIL", settings))

    def test_system_enabled(self):
        settings = MagicMock()
        settings.system_enabled = True
        self.assertTrue(channel_allowed("SYSTEM", settings))

    def test_unknown_channel_allowed(self):
        settings = MagicMock()
        self.assertTrue(channel_allowed("UNKNOWN_CHANNEL", settings))


class TestParseTimeStr(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(parse_time_str("22:30"), time(22, 30))

    def test_none(self):
        self.assertIsNone(parse_time_str(None))

    def test_invalid(self):
        self.assertIsNone(parse_time_str("invalid"))


class TestIsQuietHours(unittest.TestCase):

    def test_no_settings(self):
        self.assertFalse(is_quiet_hours(None, datetime.now()))

    def test_within_quiet_hours(self):
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"
        current = datetime(2025, 1, 1, 23, 0)
        self.assertTrue(is_quiet_hours(settings, current))

    def test_outside_quiet_hours(self):
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"
        current = datetime(2025, 1, 1, 12, 0)
        self.assertFalse(is_quiet_hours(settings, current))

    def test_same_day_range(self):
        settings = MagicMock()
        settings.quiet_hours_start = "12:00"
        settings.quiet_hours_end = "14:00"
        current = datetime(2025, 1, 1, 13, 0)
        self.assertTrue(is_quiet_hours(settings, current))


class TestNextQuietResume(unittest.TestCase):

    def test_resume_today(self):
        settings = MagicMock()
        settings.quiet_hours_end = "08:00"
        current = datetime(2025, 1, 1, 3, 0)
        result = next_quiet_resume(settings, current)
        self.assertEqual(result.hour, 8)
        self.assertEqual(result.day, 1)

    def test_resume_tomorrow(self):
        settings = MagicMock()
        settings.quiet_hours_end = "08:00"
        current = datetime(2025, 1, 1, 10, 0)
        result = next_quiet_resume(settings, current)
        self.assertEqual(result.day, 2)

    def test_no_end_time(self):
        settings = MagicMock()
        settings.quiet_hours_end = None
        current = datetime(2025, 1, 1, 10, 0)
        result = next_quiet_resume(settings, current)
        self.assertEqual(result, current + timedelta(minutes=30))


if __name__ == "__main__":
    unittest.main()
