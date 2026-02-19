# -*- coding: utf-8 -*-
"""Unit tests for app/services/alert_rule_engine/base.py - batch 41"""
import pytest

pytest.importorskip("app.services.alert_rule_engine.base")

from unittest.mock import MagicMock, patch


@pytest.fixture
def engine():
    with patch("app.services.alert_rule_engine.base.AlertLevelEnum") as mock_enum:
        mock_enum.INFO = MagicMock(value="INFO")
        mock_enum.WARNING = MagicMock(value="WARNING")
        mock_enum.CRITICAL = MagicMock(value="CRITICAL")
        mock_enum.URGENT = MagicMock(value="URGENT")
        from app.services.alert_rule_engine.base import AlertRuleEngineBase
        return AlertRuleEngineBase()


def test_level_priority_warning(engine):
    result = engine.level_priority("WARNING")
    assert result == 2


def test_level_priority_critical(engine):
    result = engine.level_priority("CRITICAL")
    assert result == 3


def test_level_priority_unknown(engine):
    result = engine.level_priority("UNKNOWN_LEVEL")
    assert result == 0


def test_get_field_value_flat(engine):
    data = {"name": "test", "value": 42}
    result = engine.get_field_value("name", data)
    assert result == "test"


def test_get_field_value_nested(engine):
    data = {"project": {"progress": 75}}
    result = engine.get_field_value("project.progress", data)
    assert result == 75


def test_get_field_value_from_context(engine):
    data = {}
    context = {"days_delay": 5}
    result = engine.get_field_value("days_delay", data, context)
    assert result == 5


def test_get_field_value_missing_returns_none(engine):
    data = {"foo": "bar"}
    result = engine.get_field_value("nonexistent.key", data)
    assert result is None


def test_get_nested_value_attribute_access(engine):
    obj = MagicMock()
    obj.status = "active"
    data = {"item": obj}
    # Test that attribute access works for nested objects
    result = engine._get_nested_value("item", data)
    assert result is obj
