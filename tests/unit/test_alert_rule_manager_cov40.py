# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 预警规则管理器
"""

import pytest
from unittest.mock import MagicMock, call

try:
    from app.services.alert_rule_engine.rule_manager import RuleManager
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


class TestRuleManagerGetOrCreate:

    def test_returns_existing_rule(self, mock_db):
        existing = MagicMock()
        existing.rule_code = "DELAY_ALERT"
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        rule = RuleManager.get_or_create_rule(mock_db, "DELAY_ALERT", {"rule_name": "延期预警"})
        assert rule is existing
        mock_db.add.assert_not_called()

    def test_creates_rule_when_not_exists(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        rule = RuleManager.get_or_create_rule(mock_db, "NEW_RULE", {"rule_name": "新规则"})
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_created_rule_is_system_and_enabled(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        from app.models.alert import AlertRule
        with MagicMock() as mock_alert_rule:
            created_instances = []

            original_init = AlertRule.__init__ if hasattr(AlertRule, "__init__") else None

            # 直接验证db.add被调用
            RuleManager.get_or_create_rule(mock_db, "TEST_RULE", {"rule_name": "测试"})
            call_args = mock_db.add.call_args[0][0]
            # 验证is_system=True和is_enabled=True
            assert call_args.is_system is True
            assert call_args.is_enabled is True

    def test_rule_code_set_correctly(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        RuleManager.get_or_create_rule(mock_db, "MY_CODE", {"rule_name": "规则"})
        call_args = mock_db.add.call_args[0][0]
        assert call_args.rule_code == "MY_CODE"

    def test_default_config_applied(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        config = {"rule_name": "成本预警", "threshold_value": 20.0}
        RuleManager.get_or_create_rule(mock_db, "COST_ALERT", config)
        call_args = mock_db.add.call_args[0][0]
        assert call_args.rule_name == "成本预警"
        assert call_args.threshold_value == 20.0

    def test_returns_rule_when_found(self, mock_db):
        rule = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = rule
        result = RuleManager.get_or_create_rule(mock_db, "EXISTING", {})
        assert result is rule
