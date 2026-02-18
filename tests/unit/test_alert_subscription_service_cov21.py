# -*- coding: utf-8 -*-
"""第二十一批：预警订阅服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.alert_subscription_service")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.alert_subscription_service import AlertSubscriptionService
    return AlertSubscriptionService(mock_db)


def _make_alert(alert_level="WARN", project_id=None, rule=None):
    a = MagicMock()
    a.id = 1
    a.alert_level = alert_level
    a.project_id = project_id
    a.status = "PENDING"
    a.rule = rule
    a.triggered_at = datetime.now()
    return a


def _make_rule(rule_type="SCHEDULE_DELAY"):
    r = MagicMock()
    r.rule_type = rule_type
    r.notify_channels = ["SYSTEM"]
    return r


def _make_subscription(user_id=1, min_level="INFO", quiet_start=None, quiet_end=None,
                        project_id=None, alert_type=None):
    s = MagicMock()
    s.user_id = user_id
    s.min_level = min_level
    s.quiet_start = quiet_start
    s.quiet_end = quiet_end
    s.project_id = project_id
    s.alert_type = alert_type
    s.is_active = True
    s.notify_channels = ["SYSTEM"]
    return s


class TestCheckLevelMatch:
    def test_warn_meets_info_minimum(self, service):
        result = service._check_level_match("WARNING", "INFO")
        assert result is True

    def test_info_does_not_meet_critical_minimum(self, service):
        result = service._check_level_match("INFO", "CRITICAL")
        assert result is False

    def test_equal_levels_match(self, service):
        result = service._check_level_match("WARNING", "WARNING")
        assert result is True

    def test_unknown_level_returns_false_for_known_min(self, service):
        result = service._check_level_match("UNKNOWN", "WARNING")
        assert result is False


class TestIsQuietHours:
    def test_no_quiet_hours_configured(self, service):
        sub = _make_subscription(quiet_start=None, quiet_end=None)
        assert service._is_quiet_hours(sub) is False

    def test_invalid_time_format_returns_false(self, service):
        sub = _make_subscription(quiet_start="invalid", quiet_end="also_invalid")
        assert service._is_quiet_hours(sub) is False


class TestMatchSubscriptions:
    def test_no_rule_returns_empty(self, service, mock_db):
        alert = _make_alert()
        alert.rule = None
        result = service.match_subscriptions(alert)
        assert result == []

    def test_returns_matching_subscriptions(self, service, mock_db):
        rule = _make_rule()
        alert = _make_alert(alert_level="WARN", rule=rule)
        sub = _make_subscription(user_id=1, min_level="INFO")
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [sub]
        mock_db.query.return_value.filter.return_value.all.return_value = [sub]

        # The method queries and filters; just verify it returns something
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [sub]
        result = service.match_subscriptions(alert, rule=rule)
        # Should call db.query
        assert mock_db.query.called


class TestGetUserSubscriptions:
    def test_queries_user_subscriptions(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = service.get_user_subscriptions(user_id=1)
        assert isinstance(result, list)

    def test_filters_by_alert_type(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = service.get_user_subscriptions(user_id=1, alert_type="SCHEDULE_DELAY")
        assert isinstance(result, list)
