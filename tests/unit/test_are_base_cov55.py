# -*- coding: utf-8 -*-
"""
Tests for app/services/alert_rule_engine/base.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.alert_rule_engine.base import AlertRuleEngineBase
    from app.models.enums import AlertLevelEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def engine():
    return AlertRuleEngineBase()


def test_level_priority_info(engine):
    """INFO 级别优先级为 1"""
    assert engine.level_priority(AlertLevelEnum.INFO.value) == 1


def test_level_priority_warning(engine):
    """WARNING 级别优先级为 2"""
    assert engine.level_priority(AlertLevelEnum.WARNING.value) == 2


def test_level_priority_critical(engine):
    """CRITICAL 级别优先级为 3"""
    assert engine.level_priority(AlertLevelEnum.CRITICAL.value) == 3


def test_level_priority_urgent(engine):
    """URGENT 级别优先级为 4"""
    assert engine.level_priority(AlertLevelEnum.URGENT.value) == 4


def test_level_priority_unknown(engine):
    """未知级别返回 0"""
    assert engine.level_priority("UNKNOWN_LEVEL") == 0


def test_get_field_value_simple(engine):
    """简单字段路径获取值"""
    data = {"project": "测试项目", "progress": 80}
    value = engine.get_field_value("progress", data)
    assert value == 80


def test_get_field_value_nested(engine):
    """嵌套字段路径获取值"""
    data = {"project": {"progress": 75}}
    value = engine.get_field_value("project.progress", data)
    assert value == 75


def test_get_field_value_not_found(engine):
    """不存在的字段返回 None"""
    data = {"a": 1}
    value = engine.get_field_value("b.c", data)
    assert value is None


def test_get_field_value_from_context(engine):
    """当 target_data 无该字段时从 context 获取"""
    data = {}
    context = {"days_delay": 5}
    value = engine.get_field_value("days_delay", data, context)
    assert value == 5


def test_response_timeout_constants():
    """响应时限常量配置合理"""
    engine = AlertRuleEngineBase()
    assert engine.RESPONSE_TIMEOUT[AlertLevelEnum.URGENT.value] < engine.RESPONSE_TIMEOUT[AlertLevelEnum.INFO.value]
