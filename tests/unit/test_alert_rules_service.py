# -*- coding: utf-8 -*-
"""AlertRulesService 单元测试"""
from unittest.mock import MagicMock, patch
import pytest

from app.services.alert.alert_rules_service import AlertRulesService


class TestAlertRulesService:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = AlertRulesService(self.db)

    def test_get_alert_rule(self):
        rule = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = rule
        assert self.svc.get_alert_rule(1) is rule

    def test_get_alert_rule_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.svc.get_alert_rule(999) is None

    def test_delete_alert_rule_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.svc.delete_alert_rule(999) is False

    def test_delete_alert_rule_success(self):
        rule = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = rule
        assert self.svc.delete_alert_rule(1) is True
        self.db.delete.assert_called_once_with(rule)

    def test_toggle_alert_rule_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        user = MagicMock()
        assert self.svc.toggle_alert_rule(999, user) is None

    def test_toggle_alert_rule_success(self):
        rule = MagicMock()
        rule.is_enabled = True
        self.db.query.return_value.filter.return_value.first.return_value = rule
        user = MagicMock()
        user.id = 1
        result = self.svc.toggle_alert_rule(1, user)
        assert result.is_enabled is False

    def test_generate_rule_code(self):
        self.db.query.return_value.filter.return_value.count.return_value = 0
        code = self.svc._generate_rule_code("project_delay")
        assert code.startswith("PD")

    def test_generate_rule_code_unknown_type(self):
        self.db.query.return_value.filter.return_value.count.return_value = 0
        code = self.svc._generate_rule_code("unknown_type")
        assert code.startswith("AL")
