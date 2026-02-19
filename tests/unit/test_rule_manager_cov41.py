# -*- coding: utf-8 -*-
"""Unit tests for app/services/alert_rule_engine/rule_manager.py - batch 41"""
import pytest

pytest.importorskip("app.services.alert_rule_engine.rule_manager")

from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


def test_get_or_create_rule_existing(mock_db):
    from app.services.alert_rule_engine.rule_manager import RuleManager

    existing_rule = MagicMock()
    existing_rule.rule_code = "TEST_RULE"
    mock_db.query.return_value.filter.return_value.first.return_value = existing_rule

    result = RuleManager.get_or_create_rule(
        mock_db,
        "TEST_RULE",
        {"rule_name": "Test", "description": "test"}
    )

    assert result is existing_rule
    mock_db.add.assert_not_called()


def test_get_or_create_rule_creates_new(mock_db):
    from app.services.alert_rule_engine.rule_manager import RuleManager

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.alert_rule_engine.rule_manager.AlertRule") as MockRule:
        new_rule = MagicMock()
        MockRule.return_value = new_rule

        result = RuleManager.get_or_create_rule(
            mock_db,
            "NEW_RULE",
            {"rule_name": "New Rule"}
        )

        MockRule.assert_called_once_with(
            rule_code="NEW_RULE",
            is_system=True,
            is_enabled=True,
            rule_name="New Rule"
        )
        mock_db.add.assert_called_once_with(new_rule)
        mock_db.flush.assert_called_once()
        assert result is new_rule


def test_get_or_create_rule_is_static():
    from app.services.alert_rule_engine.rule_manager import RuleManager
    # Verify it's a static method
    assert isinstance(
        RuleManager.__dict__["get_or_create_rule"],
        staticmethod
    )


def test_get_or_create_rule_uses_filter_by_code(mock_db):
    from app.services.alert_rule_engine.rule_manager import RuleManager

    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

    RuleManager.get_or_create_rule(mock_db, "MY_CODE", {})
    mock_db.query.assert_called_once()


def test_get_or_create_rule_default_config_fields(mock_db):
    from app.services.alert_rule_engine.rule_manager import RuleManager

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.alert_rule_engine.rule_manager.AlertRule") as MockRule:
        MockRule.return_value = MagicMock()
        RuleManager.get_or_create_rule(
            mock_db,
            "TEST",
            {"rule_name": "Test", "level": "WARNING", "threshold": 80}
        )
        call_kwargs = MockRule.call_args[1]
        assert call_kwargs["is_system"] is True
        assert call_kwargs["is_enabled"] is True
        assert call_kwargs["rule_name"] == "Test"
        assert call_kwargs["level"] == "WARNING"
