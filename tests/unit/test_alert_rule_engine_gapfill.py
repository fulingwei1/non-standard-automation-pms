# -*- coding: utf-8 -*-
"""alert rule engine 余下分支补测。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.enums import AlertLevelEnum
from app.services.alert.rule_engine import AlertRuleEngine
from app.services.alert.rule_engine.alert_generator import AlertGenerator
from app.services.alert.rule_engine.base import AlertRuleEngineBase
from app.services.alert.rule_engine.level_determiner import LevelDeterminer
from app.services.alert.rule_engine import alert_generator as ag_module
from app.services.alert.rule_engine import rule_manager as rm_module


def test_base_helpers_cover_context_attr_and_unknown_level():
    base = AlertRuleEngineBase()

    assert base.level_priority("UNKNOWN") == 0
    assert base.get_field_value("user.name", {}, {"user": SimpleNamespace(name="张三")}) == "张三"
    assert base._get_nested_value("user.missing", {"user": SimpleNamespace(name="张三")}) is None


def test_generate_alert_no_uses_rule_prefix_and_count(monkeypatch):
    class FixedDateTime:
        @staticmethod
        def now():
            class _Now:
                @staticmethod
                def strftime(fmt):
                    return "20260411"

            return _Now()

    query = MagicMock()
    query.count.return_value = 12
    db = MagicMock()
    db.query.return_value = query

    monkeypatch.setattr(ag_module, "datetime", FixedDateTime)
    monkeypatch.setattr(ag_module, "apply_like_filter", lambda q, model, pattern, field, use_ilike=False: q)

    rule = SimpleNamespace(rule_code="abc001")
    result = AlertGenerator.generate_alert_no(db, rule, {"target_id": 1})

    assert result == "ABC202604110013"


def test_level_determiner_returns_fallback_warning():
    assert (
        LevelDeterminer.determine_alert_level(SimpleNamespace(alert_level=None), {})
        == AlertLevelEnum.WARNING.value
    )


def test_rule_manager_returns_existing_rule():
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = "existing-rule"

    result = rm_module.RuleManager.get_or_create_rule(db, "R001", {"rule_name": "规则"})

    assert result == "existing-rule"
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_rule_manager_creates_rule_when_missing(monkeypatch):
    class FakeAlertRule:
        rule_code = "RULE_CODE_FIELD"

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = None
    monkeypatch.setattr(rm_module, "AlertRule", FakeAlertRule)

    result = rm_module.RuleManager.get_or_create_rule(db, "R002", {"rule_name": "新规则"})

    assert isinstance(result, FakeAlertRule)
    assert result.rule_code == "R002"
    assert result.is_system is True
    assert result.is_enabled is True
    assert result.rule_name == "新规则"
    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()


def test_alert_rule_engine_init_and_evaluate_paths(monkeypatch):
    creator_init = MagicMock()
    upgrader_init = MagicMock()
    monkeypatch.setattr("app.services.alert.rule_engine.AlertCreator.__init__", creator_init)
    monkeypatch.setattr("app.services.alert.rule_engine.AlertUpgrader.__init__", upgrader_init)

    db = MagicMock()
    engine = AlertRuleEngine(db)
    creator_init.assert_called_once_with(engine, db)
    upgrader_init.assert_called_once_with(engine, db)

    disabled_rule = SimpleNamespace(is_enabled=False)
    assert engine.evaluate_rule(disabled_rule, {}) is None

    rule = SimpleNamespace(is_enabled=True, alert_level="WARNING")
    engine.check_condition = MagicMock(return_value=False)
    assert engine.evaluate_rule(rule, {}) is None

    engine.check_condition = MagicMock(return_value=True)
    monkeypatch.setattr(
        "app.services.alert.rule_engine.LevelDeterminer.determine_alert_level",
        lambda *args, **kwargs: "CRITICAL",
    )

    existing_alert = SimpleNamespace(alert_level="WARNING")
    engine.should_create_alert = MagicMock(return_value=existing_alert)
    engine.level_priority = MagicMock(side_effect=lambda x: {"WARNING": 1, "CRITICAL": 2}.get(x, 0))
    engine.upgrade_alert = MagicMock(return_value="upgraded")
    assert engine.evaluate_rule(rule, {"id": 1}) == "upgraded"

    existing_alert_same = SimpleNamespace(alert_level="CRITICAL")
    engine.should_create_alert = MagicMock(return_value=existing_alert_same)
    engine.level_priority = MagicMock(side_effect=lambda x: {"WARNING": 1, "CRITICAL": 2}.get(x, 0))
    assert engine.evaluate_rule(rule, {"id": 2}) is None

    engine.should_create_alert = MagicMock(return_value=None)
    engine.create_alert = MagicMock(return_value="created")
    assert engine.evaluate_rule(rule, {"id": 3}) == "created"
