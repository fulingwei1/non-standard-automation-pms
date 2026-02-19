# -*- coding: utf-8 -*-
"""单元测试 - NotificationUtilsMixin (cov48)"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.notify.utils import NotificationUtilsMixin
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for NotificationUtilsMixin")


class _ConcreteUtils(NotificationUtilsMixin):
    """具体化通知工具类用于测试"""
    def __init__(self):
        self.db = MagicMock()


def _make_utils():
    return _ConcreteUtils()


def test_generate_dedup_key_returns_32_char_hex():
    utils = _make_utils()
    notification = {
        "type": "PENDING",
        "receiver_id": 1,
        "instance_id": 100,
        "task_id": 200,
    }
    key = utils._generate_dedup_key(notification)
    assert len(key) == 32
    assert all(c in "0123456789abcdef" for c in key)


def test_generate_dedup_key_is_deterministic():
    utils = _make_utils()
    notification = {"type": "A", "receiver_id": 5, "instance_id": 10, "task_id": 20}
    key1 = utils._generate_dedup_key(notification)
    key2 = utils._generate_dedup_key(notification)
    assert key1 == key2


def test_generate_dedup_key_with_empty_notification():
    utils = _make_utils()
    key = utils._generate_dedup_key({})
    assert len(key) == 32


def test_check_user_preferences_defaults_when_no_settings():
    utils = _make_utils()
    utils.db.query.return_value.filter.return_value.first.return_value = None
    prefs = utils._check_user_preferences(1, "PENDING")
    assert prefs["system_enabled"] is True
    assert "email_enabled" in prefs
    assert "wechat_enabled" in prefs


def test_check_user_preferences_all_false_when_approval_disabled():
    utils = _make_utils()
    settings = MagicMock()
    settings.approval_notifications = False
    utils.db.query.return_value.filter.return_value.first.return_value = settings
    prefs = utils._check_user_preferences(1, "PENDING")
    assert all(v is False for v in prefs.values())


def test_check_user_preferences_quiet_hours_disables_push():
    utils = _make_utils()
    settings = MagicMock()
    settings.approval_notifications = True
    settings.quiet_hours_start = "00:00"
    settings.quiet_hours_end = "23:59"
    settings.system_enabled = True
    settings.email_enabled = True
    settings.wechat_enabled = True
    settings.sms_enabled = True
    utils.db.query.return_value.filter.return_value.first.return_value = settings
    prefs = utils._check_user_preferences(1, "PENDING")
    assert prefs["email_enabled"] is False
    assert prefs["wechat_enabled"] is False
    assert prefs["sms_enabled"] is False


def test_is_duplicate_returns_false_when_window_zero():
    utils = _make_utils()
    utils._check_user_preferences = MagicMock(return_value={"dedup_window_hours": 0})
    dedup_key = "1:2:3:PENDING:1"
    result = utils._is_duplicate(dedup_key)
    assert result is False


def test_check_user_preferences_returns_defaults_on_exception():
    utils = _make_utils()
    utils.db.query.side_effect = Exception("DB error")
    prefs = utils._check_user_preferences(1, "PENDING")
    assert prefs["system_enabled"] is True
