# -*- coding: utf-8 -*-
"""
Tests for alert_rule_engine/base service
Covers: app/services/alert_rule_engine/base.py
"""

from app.services.alert_rule_engine.base import AlertRuleEngineBase


class TestAlertRuleEngineBase:
    """Test suite for AlertRuleEngineBase."""

    def test_init(self):
        """测试服务初始化"""
        service = AlertRuleEngineBase()
        assert service is not None

    def test_level_priority(self):
        """测试 level_priority 方法"""
        service = AlertRuleEngineBase()
        # URGENT 优先级最高
        assert service.level_priority("URGENT") == 4
        assert service.level_priority("CRITICAL") == 3
        assert service.level_priority("WARNING") == 2
        assert service.level_priority("INFO") == 1
        # 未知级别返回 0
        assert service.level_priority("UNKNOWN") == 0

    def test_get_field_value_flat(self):
        """测试 get_field_value - 平铺数据"""
        service = AlertRuleEngineBase()
        data = {"name": "test", "value": 42}
        assert service.get_field_value("name", data) == "test"
        assert service.get_field_value("value", data) == 42
        assert service.get_field_value("missing", data) is None

    def test_get_field_value_nested(self):
        """测试 get_field_value - 嵌套数据"""
        service = AlertRuleEngineBase()
        data = {"project": {"progress": 80, "name": "P1"}}
        assert service.get_field_value("project.progress", data) == 80
        assert service.get_field_value("project.name", data) == "P1"
        assert service.get_field_value("project.missing", data) is None

    def test_get_field_value_with_context(self):
        """测试 get_field_value - 使用上下文"""
        service = AlertRuleEngineBase()
        data = {"name": "test"}
        context = {"threshold": 90}
        # 先在 data 中查找
        assert service.get_field_value("name", data, context) == "test"
        # data 中没有则在 context 中查找
        assert service.get_field_value("threshold", data, context) == 90

    def test_response_timeout(self):
        """测试响应时限配置"""
        service = AlertRuleEngineBase()
        assert service.RESPONSE_TIMEOUT["URGENT"] == 1
        assert service.RESPONSE_TIMEOUT["CRITICAL"] == 4
        assert service.RESPONSE_TIMEOUT["WARNING"] == 8
        assert service.RESPONSE_TIMEOUT["INFO"] == 24
