# -*- coding: utf-8 -*-
"""预警内容生成器单元测试 - 第三十六批"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.alert_rule_engine.alert_generator")

try:
    from app.services.alert_rule_engine.alert_generator import AlertGenerator
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    AlertGenerator = None


def make_rule(rule_code="ALR", rule_name="测试预警", **kwargs):
    rule = MagicMock()
    rule.rule_code = rule_code
    rule.rule_name = rule_name
    rule.rule_type = kwargs.get("rule_type", "THRESHOLD")
    return rule


def make_db(count=0):
    db = MagicMock()
    db.query.return_value.count.return_value = count
    # apply_like_filter 可能修改query链
    mock_filtered = MagicMock()
    mock_filtered.count.return_value = count
    db.query.return_value = mock_filtered
    return db


class TestGenerateAlertNo:
    @patch("app.services.alert_rule_engine.alert_generator.apply_like_filter")
    def test_generates_alert_no_format(self, mock_filter):
        db = MagicMock()
        mock_chain = MagicMock()
        mock_chain.count.return_value = 0
        mock_filter.return_value = mock_chain
        db.query.return_value = mock_chain

        rule = make_rule(rule_code="SHORTAGE")
        result = AlertGenerator.generate_alert_no(db, rule, {"target_name": "项目A"})
        assert result.startswith("SHO")
        today = datetime.now().strftime('%Y%m%d')
        assert today in result

    @patch("app.services.alert_rule_engine.alert_generator.apply_like_filter")
    def test_alert_no_with_existing_count(self, mock_filter):
        db = MagicMock()
        mock_chain = MagicMock()
        mock_chain.count.return_value = 5
        mock_filter.return_value = mock_chain
        db.query.return_value = mock_chain

        rule = make_rule(rule_code="MAT")
        result = AlertGenerator.generate_alert_no(db, rule, {})
        assert result.endswith("0006")


class TestGenerateAlertTitle:
    def test_uses_target_name(self):
        rule = make_rule(rule_name="缺料预警")
        target_data = {"target_name": "项目X"}
        result = AlertGenerator.generate_alert_title(rule, target_data, "WARNING")
        assert "缺料预警" in result
        assert "项目X" in result

    def test_falls_back_to_target_no(self):
        rule = make_rule(rule_name="延期预警")
        target_data = {"target_no": "P-001"}
        result = AlertGenerator.generate_alert_title(rule, target_data, "CRITICAL")
        assert "P-001" in result

    def test_no_target_uses_default(self):
        rule = make_rule(rule_name="质量预警")
        result = AlertGenerator.generate_alert_title(rule, {}, "WARNING")
        assert "对象" in result

    def test_context_accepted(self):
        rule = make_rule(rule_name="测试")
        result = AlertGenerator.generate_alert_title(rule, {"target_name": "T"}, "INFO", context={"key": "val"})
        assert isinstance(result, str)
