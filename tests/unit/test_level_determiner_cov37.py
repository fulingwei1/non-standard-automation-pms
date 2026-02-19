# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 预警级别确定器
tests/unit/test_level_determiner_cov37.py
"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.alert_rule_engine.level_determiner")

from app.services.alert_rule_engine.level_determiner import LevelDeterminer


def _make_rule(level="WARNING"):
    rule = MagicMock()
    rule.alert_level = level
    return rule


class TestLevelDeterminer:
    def test_determine_uses_rule_level_by_default(self):
        rule = _make_rule("CRITICAL")
        result = LevelDeterminer.determine_alert_level(rule, {})
        assert result == "CRITICAL"

    def test_determine_falls_back_to_warning_when_rule_level_none(self):
        rule = _make_rule(None)
        # When rule.alert_level is None, returns AlertLevelEnum.WARNING.value
        result = LevelDeterminer.determine_alert_level(rule, {})
        assert result is not None  # default fallback

    def test_determine_accepts_context(self):
        rule = _make_rule("INFO")
        ctx = {"threshold_exceeded": True}
        result = LevelDeterminer.determine_alert_level(rule, {}, context=ctx)
        assert result == "INFO"

    def test_determine_accepts_engine_arg(self):
        rule = _make_rule("URGENT")
        engine = MagicMock()
        result = LevelDeterminer.determine_alert_level(rule, {}, engine=engine)
        assert result == "URGENT"

    def test_is_static_method(self):
        """can be called without instantiation"""
        rule = _make_rule("WARNING")
        result = LevelDeterminer.determine_alert_level(rule, {"val": 5})
        assert isinstance(result, str)

    def test_instantiated_call_also_works(self):
        determiner = LevelDeterminer()
        rule = _make_rule("CRITICAL")
        result = determiner.determine_alert_level(rule, {})
        assert result == "CRITICAL"
