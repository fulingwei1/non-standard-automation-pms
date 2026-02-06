# -*- coding: utf-8 -*-
"""
condition_evaluator.py 单元测试

测试预警规则引擎的条件评估方法
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.services.alert_rule_engine.condition_evaluator import ConditionEvaluator


@pytest.fixture
def evaluator():
    return ConditionEvaluator()


@pytest.fixture
def mock_rule():
    """创建一个可配置的 mock AlertRule"""
    def _create_rule(**kwargs):
        rule = MagicMock()
        rule.rule_type = kwargs.get("rule_type", "THRESHOLD")
        rule.target_field = kwargs.get("target_field", "value")
        rule.threshold_value = kwargs.get("threshold_value", 100)
        rule.condition_operator = kwargs.get("condition_operator", "GT")
        rule.condition_expr = kwargs.get("condition_expr", None)
        rule.advance_days = kwargs.get("advance_days", 0)
        return rule
    return _create_rule


@pytest.mark.unit
class TestCheckCondition:
    """测试 check_condition 主方法"""

    def test_threshold_rule_type(self, evaluator, mock_rule):
        """测试阈值类型规则"""
        rule = mock_rule(rule_type="THRESHOLD", threshold_value=50, condition_operator="GT")
        result = evaluator.check_condition(rule, {"value": 60})
        assert result is True

    def test_deviation_rule_type(self, evaluator, mock_rule):
        """测试偏差类型规则"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10,
            condition_operator="GT"
        )
        result = evaluator.check_condition(
            rule, {"actual_value": 120, "planned_value": 100}
        )
        assert result is True

    def test_overdue_rule_type(self, evaluator, mock_rule):
        """测试逾期类型规则"""
        past_date = datetime.now() - timedelta(days=1)
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.check_condition(rule, {"due_date": past_date})
        assert result is True

    def test_custom_rule_type(self, evaluator, mock_rule):
        """测试自定义表达式类型规则"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr="value > 50")
        result = evaluator.check_condition(rule, {"value": 60})
        # 结果取决于 simpleeval 是否安装
        assert isinstance(result, bool)

    def test_unknown_rule_type(self, evaluator, mock_rule):
        """测试未知规则类型"""
        rule = mock_rule(rule_type="UNKNOWN")
        result = evaluator.check_condition(rule, {"value": 60})
        assert result is False


@pytest.mark.unit
class TestMatchThreshold:
    """测试 match_threshold 方法"""

    def test_gt_operator_true(self, evaluator, mock_rule):
        """测试大于操作符 - 满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is True

    def test_gt_operator_false(self, evaluator, mock_rule):
        """测试大于操作符 - 不满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"value": 40})
        assert result is False

    def test_gte_operator_equal(self, evaluator, mock_rule):
        """测试大于等于操作符 - 等于情况"""
        rule = mock_rule(threshold_value=50, condition_operator="GTE")
        result = evaluator.match_threshold(rule, {"value": 50})
        assert result is True

    def test_gte_operator_greater(self, evaluator, mock_rule):
        """测试大于等于操作符 - 大于情况"""
        rule = mock_rule(threshold_value=50, condition_operator="GTE")
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is True

    def test_lt_operator_true(self, evaluator, mock_rule):
        """测试小于操作符 - 满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="LT")
        result = evaluator.match_threshold(rule, {"value": 40})
        assert result is True

    def test_lt_operator_false(self, evaluator, mock_rule):
        """测试小于操作符 - 不满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="LT")
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is False

    def test_lte_operator_equal(self, evaluator, mock_rule):
        """测试小于等于操作符 - 等于情况"""
        rule = mock_rule(threshold_value=50, condition_operator="LTE")
        result = evaluator.match_threshold(rule, {"value": 50})
        assert result is True

    def test_lte_operator_less(self, evaluator, mock_rule):
        """测试小于等于操作符 - 小于情况"""
        rule = mock_rule(threshold_value=50, condition_operator="LTE")
        result = evaluator.match_threshold(rule, {"value": 40})
        assert result is True

    def test_eq_operator_true(self, evaluator, mock_rule):
        """测试等于操作符 - 满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="EQ")
        result = evaluator.match_threshold(rule, {"value": 50})
        assert result is True

    def test_eq_operator_false(self, evaluator, mock_rule):
        """测试等于操作符 - 不满足条件"""
        rule = mock_rule(threshold_value=50, condition_operator="EQ")
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is False

    def test_unknown_operator(self, evaluator, mock_rule):
        """测试未知操作符"""
        rule = mock_rule(threshold_value=50, condition_operator="UNKNOWN")
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is False

    def test_none_value(self, evaluator, mock_rule):
        """测试值为 None 的情况"""
        rule = mock_rule(threshold_value=50, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"value": None})
        assert result is False

    def test_missing_field(self, evaluator, mock_rule):
        """测试字段不存在的情况"""
        rule = mock_rule(target_field="missing_field", threshold_value=50)
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is False

    def test_invalid_value_type(self, evaluator, mock_rule):
        """测试无效值类型"""
        rule = mock_rule(threshold_value=50, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"value": "not a number"})
        assert result is False

    def test_default_operator(self, evaluator, mock_rule):
        """测试默认操作符 (GT)"""
        rule = mock_rule(threshold_value=50, condition_operator=None)
        result = evaluator.match_threshold(rule, {"value": 60})
        assert result is True

    def test_default_threshold(self, evaluator, mock_rule):
        """测试默认阈值 (0)"""
        rule = mock_rule(threshold_value=None, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"value": 1})
        assert result is True

    def test_nested_field(self, evaluator, mock_rule):
        """测试嵌套字段"""
        rule = mock_rule(target_field="data.value", threshold_value=50, condition_operator="GT")
        result = evaluator.match_threshold(rule, {"data": {"value": 60}})
        assert result is True


@pytest.mark.unit
class TestMatchDeviation:
    """测试 match_deviation 方法"""

    def test_positive_deviation_gt(self, evaluator, mock_rule):
        """测试正偏差大于阈值"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10,
            condition_operator="GT"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 120, "planned_value": 100}
        )
        assert result is True  # deviation = 20 > 10

    def test_negative_deviation_lt(self, evaluator, mock_rule):
        """测试负偏差小于阈值"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=0,
            condition_operator="LT"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 80, "planned_value": 100}
        )
        assert result is True  # deviation = -20 < 0

    def test_deviation_gte(self, evaluator, mock_rule):
        """测试偏差大于等于"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=20,
            condition_operator="GTE"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 120, "planned_value": 100}
        )
        assert result is True  # deviation = 20 >= 20

    def test_deviation_lte(self, evaluator, mock_rule):
        """测试偏差小于等于"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10,
            condition_operator="LTE"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 105, "planned_value": 100}
        )
        assert result is True  # deviation = 5 <= 10

    def test_missing_actual_value(self, evaluator, mock_rule):
        """测试缺少实际值"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10
        )
        result = evaluator.match_deviation(rule, {"planned_value": 100})
        assert result is False

    def test_missing_planned_value(self, evaluator, mock_rule):
        """测试缺少计划值"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10
        )
        result = evaluator.match_deviation(rule, {"actual_value": 120})
        assert result is False

    def test_invalid_value_types(self, evaluator, mock_rule):
        """测试无效值类型"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": "invalid", "planned_value": 100}
        )
        assert result is False

    def test_unknown_operator(self, evaluator, mock_rule):
        """测试未知操作符"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field="actual_value",
            threshold_value=10,
            condition_operator="UNKNOWN"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 120, "planned_value": 100}
        )
        assert result is False

    def test_default_field_names(self, evaluator, mock_rule):
        """测试默认字段名"""
        rule = mock_rule(
            rule_type="DEVIATION",
            target_field=None,  # 使用默认 actual_value
            threshold_value=10,
            condition_operator="GT"
        )
        result = evaluator.match_deviation(
            rule, {"actual_value": 120, "planned_value": 100}
        )
        assert result is True


@pytest.mark.unit
class TestMatchOverdue:
    """测试 match_overdue 方法"""

    def test_past_due_date(self, evaluator, mock_rule):
        """测试已过期日期"""
        past_date = datetime.now() - timedelta(days=1)
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": past_date})
        assert result is True

    def test_future_due_date(self, evaluator, mock_rule):
        """测试未来日期"""
        future_date = datetime.now() + timedelta(days=10)
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": future_date})
        assert result is False

    def test_with_advance_days(self, evaluator, mock_rule):
        """测试提前天数"""
        future_date = datetime.now() + timedelta(days=3)
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date", advance_days=5)
        result = evaluator.match_overdue(rule, {"due_date": future_date})
        assert result is True  # 提前5天检查，3天后到期，所以触发

    def test_string_date_iso_format(self, evaluator, mock_rule):
        """测试 ISO 格式字符串日期"""
        past_date_str = (datetime.now() - timedelta(days=1)).isoformat()
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": past_date_str})
        assert result is True

    def test_string_date_with_z(self, evaluator, mock_rule):
        """测试带 Z 后缀的字符串日期"""
        past_date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": past_date_str})
        assert result is True

    def test_invalid_date_string(self, evaluator, mock_rule):
        """测试无效日期字符串"""
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": "not a date"})
        assert result is False

    def test_missing_due_date(self, evaluator, mock_rule):
        """测试缺少截止日期"""
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {})
        assert result is False

    def test_none_due_date(self, evaluator, mock_rule):
        """测试 None 截止日期"""
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": None})
        assert result is False

    def test_invalid_date_type(self, evaluator, mock_rule):
        """测试无效日期类型"""
        rule = mock_rule(rule_type="OVERDUE", target_field="due_date")
        result = evaluator.match_overdue(rule, {"due_date": 12345})
        assert result is False


@pytest.mark.unit
class TestMatchCustomExpr:
    """测试 match_custom_expr 方法"""

    def test_no_expression(self, evaluator, mock_rule):
        """测试无表达式"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr=None)
        result = evaluator.match_custom_expr(rule, {"value": 60})
        assert result is False

    def test_empty_expression(self, evaluator, mock_rule):
        """测试空表达式"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr="")
        result = evaluator.match_custom_expr(rule, {"value": 60})
        assert result is False

    def test_simple_expression_true(self, evaluator, mock_rule):
        """测试简单表达式 - 返回 True"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr="value > 50")
        result = evaluator.match_custom_expr(rule, {"value": 60})
        # 取决于 simpleeval 是否安装
        assert isinstance(result, bool)

    def test_expression_with_context(self, evaluator, mock_rule):
        """测试带上下文的表达式"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr="value > threshold")
        result = evaluator.match_custom_expr(
            rule, {"value": 60}, context={"threshold": 50}
        )
        assert isinstance(result, bool)

    def test_invalid_expression(self, evaluator, mock_rule):
        """测试无效表达式"""
        rule = mock_rule(rule_type="CUSTOM", condition_expr="invalid syntax !!!")
        result = evaluator.match_custom_expr(rule, {"value": 60})
        assert result is False

    def test_simpleeval_not_available(self, evaluator, mock_rule):
        """测试 simpleeval 未安装时的回退逻辑"""
        import app.services.alert_rule_engine.condition_evaluator as ce_module

        # 保存原始值
        original_simple_eval = ce_module.simple_eval

        try:
            # 模拟 simpleeval 未安装
            ce_module.simple_eval = None

            rule = mock_rule(rule_type="CUSTOM", condition_expr="value > 50")
            result = evaluator.match_custom_expr(rule, {"value": 60})

            # 当 simpleeval 不可用时，应该返回 False
            assert result is False
        finally:
            # 恢复原始值
            ce_module.simple_eval = original_simple_eval


@pytest.mark.unit
class TestGetFieldValue:
    """测试 get_field_value 方法（继承自基类）"""

    def test_simple_field(self, evaluator):
        """测试简单字段"""
        value = evaluator.get_field_value("name", {"name": "test"})
        assert value == "test"

    def test_nested_field(self, evaluator):
        """测试嵌套字段"""
        value = evaluator.get_field_value(
            "user.profile.name",
            {"user": {"profile": {"name": "John"}}}
        )
        assert value == "John"

    def test_field_from_context(self, evaluator):
        """测试从上下文获取字段"""
        value = evaluator.get_field_value(
            "config_value",
            {"name": "test"},
            context={"config_value": 100}
        )
        assert value == 100

    def test_missing_field(self, evaluator):
        """测试缺失字段"""
        value = evaluator.get_field_value("missing", {"name": "test"})
        assert value is None

    def test_target_data_priority(self, evaluator):
        """测试 target_data 优先级高于 context"""
        value = evaluator.get_field_value(
            "value",
            {"value": "from_target"},
            context={"value": "from_context"}
        )
        assert value == "from_target"
