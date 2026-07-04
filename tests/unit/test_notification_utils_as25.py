# -*- coding: utf-8 -*-
"""AS-25 notification utility regression contracts."""
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_legacy_notification_utils_import_path_remains_available():
    """旧代码和测试仍会 import app.services.notification_utils。"""
    import app.services.notification_utils as notification_utils

    assert notification_utils.get_alert_icon_url("INFO")


def test_resolve_recipients_does_not_invent_admin_user_when_alert_has_no_recipient():
    """没有项目/处理人/规则用户时，resolver 不能硬塞 user_id=1。"""
    from app.services.notification_utils import resolve_recipients

    db = MagicMock()
    phantom_admin = SimpleNamespace(id=1, is_active=True)
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        phantom_admin
    ]

    alert = SimpleNamespace(project=None, handler_id=None, rule=None)

    assert resolve_recipients(db, alert) == {}
    db.query.assert_not_called()
