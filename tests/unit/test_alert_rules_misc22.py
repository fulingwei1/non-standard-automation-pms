# -*- coding: utf-8 -*-
"""MISC-22: alert-rules CRUD 不能只要求登录。"""

import inspect
from pathlib import Path

from app.api.v1.endpoints.alerts import rules
from app.utils.init_permissions_data import API_PERMISSIONS


def _source(func) -> str:
    return inspect.getsource(func)


def test_alert_rule_read_routes_require_alert_read_permission():
    for func in (
        rules.read_alert_rule_templates,
        rules.read_alert_rules,
        rules.read_alert_rule,
    ):
        src = _source(func)
        assert 'security.require_permission("alert:read")' in src
        assert "security.get_current_active_user" not in src


def test_alert_rule_write_routes_require_alert_manage_permission():
    for func in (
        rules.create_alert_rule,
        rules.update_alert_rule,
        rules.toggle_alert_rule,
        rules.delete_alert_rule,
    ):
        src = _source(func)
        assert 'security.require_permission("alert:manage")' in src
        assert "security.get_current_active_user" not in src


def test_alert_permissions_are_seeded():
    codes = {item["perm_code"] for item in API_PERMISSIONS}
    assert {"alert:read", "alert:manage"} <= codes


def test_frontend_permission_constants_include_alert_manage():
    source = Path("frontend/src/hooks/usePermission.js").read_text(encoding="utf-8")
    assert "READ: 'alert:read'" in source
    assert "MANAGE: 'alert:manage'" in source
