# -*- coding: utf-8 -*-
"""
预警规则引擎服务单元测试

测试覆盖:
- AlertRuleEngineBase: 基础工具方法
- ConditionEvaluator: 条件评估
- AlertCreator: 预警创建
- AlertUpgrader: 预警升级
- AlertRuleEngine: 完整引擎
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import AlertLevelEnum


class TestAlertRuleEngineBase:
    """测试预警规则引擎基类"""

    @pytest.fixture
    def engine_base(self):
        """创建基类实例"""
        from app.services.alert_rule_engine.base import AlertRuleEngineBase
        return AlertRuleEngineBase()

    def test_level_priority_info(self, engine_base):
        """测试INFO级别优先级"""
        assert engine_base.level_priority(AlertLevelEnum.INFO.value) == 1

    def test_level_priority_warning(self, engine_base):
        """测试WARNING级别优先级"""
        assert engine_base.level_priority(AlertLevelEnum.WARNING.value) == 2

    def test_level_priority_critical(self, engine_base):
        """测试CRITICAL级别优先级"""
        assert engine_base.level_priority(AlertLevelEnum.CRITICAL.value) == 3

    def test_level_priority_urgent(self, engine_base):
        """测试URGENT级别优先级"""
        assert engine_base.level_priority(AlertLevelEnum.URGENT.value) == 4

    def test_level_priority_unknown(self, engine_base):
        """测试未知级别返回0"""
        assert engine_base.level_priority("UNKNOWN") == 0

    def test_get_field_value_simple(self, engine_base):
        """测试获取简单字段值"""
        target_data = {"value": 100, "name": "测试"}
        assert engine_base.get_field_value("value", target_data) == 100
        assert engine_base.get_field_value("name", target_data) == "测试"

    def test_get_field_value_nested(self, engine_base):
        """测试获取嵌套字段值"""
        target_data = {
            "project": {
                "progress": 80,
                "status": "进行中"
            }
        }
        assert engine_base.get_field_value("project.progress", target_data) == 80
        assert engine_base.get_field_value("project.status", target_data) == "进行中"

    def test_get_field_value_from_context(self, engine_base):
        """测试从上下文获取字段值"""
        target_data = {"value": 100}
        context = {"extra_value": 200}
        assert engine_base.get_field_value("extra_value", target_data, context) == 200

    def test_get_field_value_priority(self, engine_base):
        """测试target_data优先于context"""
        target_data = {"value": 100}
        context = {"value": 200}
        assert engine_base.get_field_value("value", target_data, context) == 100

    def test_get_field_value_not_found(self, engine_base):
        """测试字段不存在返回None"""
        target_data = {"value": 100}
        assert engine_base.get_field_value("not_exist", target_data) is None

    def test_get_field_value_none_data(self, engine_base):
        """测试空数据"""
        assert engine_base.get_field_value("value", {}) is None

    def test_get_nested_value_with_object(self, engine_base):
        """测试获取对象属性"""
        class MockObj:
            def __init__(self):
                self.value = 42

        target_data = {"obj": MockObj()}
        assert engine_base.get_field_value("obj.value", target_data) == 42


class TestConditionEvaluator:
    """测试条件评估器"""

    @pytest.fixture
    def evaluator(self, db_session):
        """创建条件评估器"""
        from app.services.alert_rule_engine.condition_evaluator import ConditionEvaluator
        return ConditionEvaluator()

    @pytest.fixture
    def mock_rule(self):
        """创建模拟规则"""
        rule = MagicMock()
        rule.is_enabled = True
        rule.threshold_value = 100
        rule.condition_operator = "GT"
        rule.target_field = "value"
        return rule

    # 阈值匹配测试
    def test_match_threshold_gt(self, evaluator, mock_rule):
        """测试阈值匹配 - 大于"""
        mock_rule.rule_type = "THRESHOLD"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 100
        mock_rule.target_field = "value"

        assert evaluator.match_threshold(mock_rule, {"value": 101}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is False
        assert evaluator.match_threshold(mock_rule, {"value": 99}) is False

    def test_match_threshold_gte(self, evaluator, mock_rule):
        """测试阈值匹配 - 大于等于"""
        mock_rule.condition_operator = "GTE"
        mock_rule.threshold_value = 100

        assert evaluator.match_threshold(mock_rule, {"value": 101}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 99}) is False

    def test_match_threshold_lt(self, evaluator, mock_rule):
        """测试阈值匹配 - 小于"""
        mock_rule.condition_operator = "LT"
        mock_rule.threshold_value = 100

        assert evaluator.match_threshold(mock_rule, {"value": 99}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is False
        assert evaluator.match_threshold(mock_rule, {"value": 101}) is False

    def test_match_threshold_lte(self, evaluator, mock_rule):
        """测试阈值匹配 - 小于等于"""
        mock_rule.condition_operator = "LTE"
        mock_rule.threshold_value = 100

        assert evaluator.match_threshold(mock_rule, {"value": 99}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 101}) is False

    def test_match_threshold_eq(self, evaluator, mock_rule):
        """测试阈值匹配 - 等于"""
        mock_rule.condition_operator = "EQ"
        mock_rule.threshold_value = 100

        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 99}) is False
        assert evaluator.match_threshold(mock_rule, {"value": 101}) is False

    def test_match_threshold_invalid_operator(self, evaluator, mock_rule):
        """测试无效操作符"""
        mock_rule.condition_operator = "INVALID"
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is False

    def test_match_threshold_none_value(self, evaluator, mock_rule):
        """测试空值"""
        assert evaluator.match_threshold(mock_rule, {"value": None}) is False
        assert evaluator.match_threshold(mock_rule, {}) is False

    def test_match_threshold_invalid_value(self, evaluator, mock_rule):
        """测试非数字值"""
        assert evaluator.match_threshold(mock_rule, {"value": "abc"}) is False

    # 偏差匹配测试
    def test_match_deviation_gt(self, evaluator, mock_rule):
        """测试偏差匹配 - 实际值大于计划值"""
        mock_rule.rule_type = "DEVIATION"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 10
        mock_rule.target_field = "actual_cost"

        target_data = {
            "actual_cost": 120,
            "planned_cost": 100
        }
        assert evaluator.match_deviation(mock_rule, target_data) is True

    def test_match_deviation_within_threshold(self, evaluator, mock_rule):
        """测试偏差在阈值内"""
        mock_rule.rule_type = "DEVIATION"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 10
        mock_rule.target_field = "actual_cost"

        target_data = {
            "actual_cost": 105,
            "planned_cost": 100
        }
        assert evaluator.match_deviation(mock_rule, target_data) is False

    def test_match_deviation_missing_values(self, evaluator, mock_rule):
        """测试偏差匹配缺少值"""
        mock_rule.target_field = "actual_value"
        assert evaluator.match_deviation(mock_rule, {"actual_value": 100}) is False
        assert evaluator.match_deviation(mock_rule, {"planned_value": 100}) is False

    # 逾期匹配测试
    def test_match_overdue_past_due(self, evaluator, mock_rule):
        """测试逾期匹配 - 已逾期"""
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0

        yesterday = datetime.now() - timedelta(days=1)
        target_data = {"due_date": yesterday.isoformat()}
        assert evaluator.match_overdue(mock_rule, target_data) is True

    def test_match_overdue_future_due(self, evaluator, mock_rule):
        """测试逾期匹配 - 未逾期"""
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0

        tomorrow = datetime.now() + timedelta(days=2)
        target_data = {"due_date": tomorrow.isoformat()}
        assert evaluator.match_overdue(mock_rule, target_data) is False

    def test_match_overdue_with_advance_days(self, evaluator, mock_rule):
        """测试逾期匹配 - 提前预警"""
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 3

        two_days_later = datetime.now() + timedelta(days=2)
        target_data = {"due_date": two_days_later.isoformat()}
        # 提前3天预警，距离到期还有2天，应该触发
        assert evaluator.match_overdue(mock_rule, target_data) is True

    def test_match_overdue_no_due_date(self, evaluator, mock_rule):
        """测试逾期匹配 - 无截止日期"""
        mock_rule.target_field = "due_date"
        assert evaluator.match_overdue(mock_rule, {}) is False
        assert evaluator.match_overdue(mock_rule, {"due_date": None}) is False

    def test_match_overdue_invalid_date_format(self, evaluator, mock_rule):
        """测试逾期匹配 - 无效日期格式"""
        mock_rule.target_field = "due_date"
        assert evaluator.match_overdue(mock_rule, {"due_date": "invalid-date"}) is False

    def test_match_overdue_datetime_object(self, evaluator, mock_rule):
        """测试逾期匹配 - datetime对象"""
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0

        yesterday = datetime.now() - timedelta(days=1)
        target_data = {"due_date": yesterday}
        assert evaluator.match_overdue(mock_rule, target_data) is True

    # 自定义表达式测试
    def test_match_custom_expr_simple(self, evaluator, mock_rule):
        """测试自定义表达式 - 简单表达式"""
        mock_rule.rule_type = "CUSTOM"
        mock_rule.condition_expr = "value > 100"

        assert evaluator.match_custom_expr(mock_rule, {"value": 101}) is True
        assert evaluator.match_custom_expr(mock_rule, {"value": 100}) is False

    def test_match_custom_expr_complex(self, evaluator, mock_rule):
        """测试自定义表达式 - 复杂表达式"""
        mock_rule.condition_expr = "progress < 50 and days_delay > 3"

        target_data = {"progress": 30, "days_delay": 5}
        assert evaluator.match_custom_expr(mock_rule, target_data) is True

        target_data = {"progress": 60, "days_delay": 5}
        assert evaluator.match_custom_expr(mock_rule, target_data) is False

    def test_match_custom_expr_no_expression(self, evaluator, mock_rule):
        """测试自定义表达式 - 无表达式"""
        mock_rule.condition_expr = None
        assert evaluator.match_custom_expr(mock_rule, {"value": 100}) is False

        mock_rule.condition_expr = ""
        assert evaluator.match_custom_expr(mock_rule, {"value": 100}) is False

    def test_match_custom_expr_invalid(self, evaluator, mock_rule):
        """测试自定义表达式 - 无效表达式"""
        mock_rule.condition_expr = "invalid syntax $$$"
        assert evaluator.match_custom_expr(mock_rule, {"value": 100}) is False

    def test_match_custom_expr_with_context(self, evaluator, mock_rule):
        """测试自定义表达式 - 使用上下文"""
        mock_rule.condition_expr = "value + extra > 100"

        target_data = {"value": 60}
        context = {"extra": 50}
        assert evaluator.match_custom_expr(mock_rule, target_data, context) is True

    # check_condition 路由测试
    def test_check_condition_threshold(self, evaluator, mock_rule):
        """测试条件检查路由 - 阈值类型"""
        mock_rule.rule_type = "THRESHOLD"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 100
        mock_rule.target_field = "value"

        assert evaluator.check_condition(mock_rule, {"value": 101}) is True
        assert evaluator.check_condition(mock_rule, {"value": 99}) is False

    def test_check_condition_deviation(self, evaluator, mock_rule):
        """测试条件检查路由 - 偏差类型"""
        mock_rule.rule_type = "DEVIATION"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 10
        mock_rule.target_field = "actual_value"

        target_data = {"actual_value": 120, "planned_value": 100}
        assert evaluator.check_condition(mock_rule, target_data) is True

    def test_check_condition_overdue(self, evaluator, mock_rule):
        """测试条件检查路由 - 逾期类型"""
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0

        yesterday = datetime.now() - timedelta(days=1)
        assert evaluator.check_condition(mock_rule, {"due_date": yesterday}) is True

    def test_check_condition_custom(self, evaluator, mock_rule):
        """测试条件检查路由 - 自定义类型"""
        mock_rule.rule_type = "CUSTOM"
        mock_rule.condition_expr = "value > 100"

        assert evaluator.check_condition(mock_rule, {"value": 101}) is True

    def test_check_condition_unknown_type(self, evaluator, mock_rule):
        """测试条件检查路由 - 未知类型"""
        mock_rule.rule_type = "UNKNOWN"
        assert evaluator.check_condition(mock_rule, {"value": 100}) is False


class TestAlertRuleEngine:
    """测试完整的预警规则引擎"""

    @pytest.fixture
    def engine(self, db_session):
        """创建预警规则引擎"""
        from app.services.alert_rule_engine import AlertRuleEngine
        return AlertRuleEngine(db_session)

    @pytest.fixture
    def mock_rule(self):
        """创建模拟规则"""
        rule = MagicMock()
        rule.id = 1
        rule.rule_code = "TEST_RULE"
        rule.rule_name = "测试规则"
        rule.rule_type = "THRESHOLD"
        rule.target_field = "value"
        rule.threshold_value = 100
        rule.condition_operator = "GT"
        rule.is_enabled = True
        rule.alert_level = AlertLevelEnum.WARNING.value
        rule.default_level = AlertLevelEnum.WARNING.value
        return rule

    def test_evaluate_rule_disabled(self, engine, mock_rule):
        """测试评估禁用规则"""
        mock_rule.is_enabled = False
        result = engine.evaluate_rule(mock_rule, {"value": 101})
        assert result is None

    def test_evaluate_rule_condition_not_met(self, engine, mock_rule):
        """测试评估条件不满足"""
        result = engine.evaluate_rule(mock_rule, {"value": 99})
        assert result is None

    def test_level_priority_comparison(self, engine):
        """测试级别优先级比较"""
        assert engine.level_priority(AlertLevelEnum.INFO.value) < engine.level_priority(AlertLevelEnum.WARNING.value)
        assert engine.level_priority(AlertLevelEnum.WARNING.value) < engine.level_priority(AlertLevelEnum.CRITICAL.value)
        assert engine.level_priority(AlertLevelEnum.CRITICAL.value) < engine.level_priority(AlertLevelEnum.URGENT.value)


class TestAlertGenerator:
    """测试预警内容生成器"""

    def test_import_alert_generator(self):
        """测试导入预警生成器"""
        from app.services.alert_rule_engine.alert_generator import AlertGenerator
        assert AlertGenerator is not None


class TestLevelDeterminer:
    """测试预警级别确定器"""

    def test_import_level_determiner(self):
        """测试导入级别确定器"""
        from app.services.alert_rule_engine.level_determiner import LevelDeterminer
        assert LevelDeterminer is not None


class TestRuleManager:
    """测试规则管理器"""

    def test_import_rule_manager(self):
        """测试导入规则管理器"""
        from app.services.alert_rule_engine.rule_manager import RuleManager
        assert RuleManager is not None
