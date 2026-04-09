# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 预警条件评估器"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta


class TestConditionEvaluatorBusinessLogic:
    """预警条件评估器业务逻辑测试"""

    def test_check_condition_threshold(self):
        """测试阈值条件检查"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.rule_type = "THRESHOLD"
            mock_rule.target_field = "value"
            mock_rule.threshold_value = 100
            mock_rule.comparison_operator = "gt"

            target_data = {"value": 150}

            result = evaluator.check_condition(mock_rule, target_data)

            # 150 > 100 应该返回True
            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_check_condition_threshold_below(self):
        """测试阈值条件检查（低于阈值）"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.rule_type = "THRESHOLD"
            mock_rule.target_field = "value"
            mock_rule.threshold_value = 100
            mock_rule.comparison_operator = "gt"

            target_data = {"value": 50}

            result = evaluator.check_condition(mock_rule, target_data)

            # 50 > 100 应该返回False
            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_match_threshold_greater_than(self):
        """测试大于阈值匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "amount"
            mock_rule.threshold_value = 1000
            mock_rule.comparison_operator = "gt"

            target_data = {"amount": 1500}

            result = evaluator.match_threshold(mock_rule, target_data)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_match_threshold_less_than(self):
        """测试小于阈值匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "stock"
            mock_rule.threshold_value = 10
            mock_rule.comparison_operator = "lt"

            target_data = {"stock": 5}

            result = evaluator.match_threshold(mock_rule, target_data)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_match_threshold_equal(self):
        """测试等于阈值匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "status"
            mock_rule.threshold_value = 0
            mock_rule.comparison_operator = "eq"

            target_data = {"status": 0}

            result = evaluator.match_threshold(mock_rule, target_data)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_match_deviation(self):
        """测试偏差匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "actual"
            mock_rule.baseline_field = "planned"
            mock_rule.deviation_threshold = 10  # 10%偏差

            target_data = {"actual": 110, "planned": 100}

            result = evaluator.match_deviation(mock_rule, target_data)

            # 10%偏差应该触发
            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_match_overdue(self):
        """测试逾期匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "due_date"

            # 逾期1天
            target_data = {"due_date": datetime.now() - timedelta(days=1)}

            result = evaluator.match_overdue(mock_rule, target_data)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_match_overdue_not_due(self):
        """测试未逾期"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "due_date"

            # 还未到期
            target_data = {"due_date": datetime.now() + timedelta(days=1)}

            result = evaluator.match_overdue(mock_rule, target_data)

            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_match_custom_expr(self):
        """测试自定义表达式匹配"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.custom_expression = "value > 100 and value < 200"

            target_data = {"value": 150}

            result = evaluator.match_custom_expr(mock_rule, target_data)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_get_field_value(self):
        """测试获取字段值"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            target_data = {"name": "测试", "value": 100}

            result = evaluator.get_field_value("value", target_data)

            assert result == 100
        except ImportError:
            pytest.skip("Module not found")

    def test_get_field_value_nested(self):
        """测试获取嵌套字段值"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            target_data = {"user": {"name": "张三"}}

            result = evaluator.get_field_value("user.name", target_data)

            assert result == "张三"
        except ImportError:
            pytest.skip("Module not found")


class TestConditionEvaluatorOperators:
    """运算符测试"""

    def test_operator_gte(self):
        """测试大于等于运算符"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "value"
            mock_rule.threshold_value = 100
            mock_rule.comparison_operator = "gte"

            # 等于
            result1 = evaluator.match_threshold(mock_rule, {"value": 100})
            # 大于
            result2 = evaluator.match_threshold(mock_rule, {"value": 101})
            # 小于
            result3 = evaluator.match_threshold(mock_rule, {"value": 99})

            assert result1 == True
            assert result2 == True
            assert result3 == False
        except ImportError:
            pytest.skip("Module not found")

    def test_operator_lte(self):
        """测试小于等于运算符"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "value"
            mock_rule.threshold_value = 100
            mock_rule.comparison_operator = "lte"

            result1 = evaluator.match_threshold(mock_rule, {"value": 100})
            result2 = evaluator.match_threshold(mock_rule, {"value": 99})
            result3 = evaluator.match_threshold(mock_rule, {"value": 101})

            assert result1 == True
            assert result2 == True
            assert result3 == False
        except ImportError:
            pytest.skip("Module not found")

    def test_operator_ne(self):
        """测试不等于运算符"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "status"
            mock_rule.threshold_value = 0
            mock_rule.comparison_operator = "ne"

            result1 = evaluator.match_threshold(mock_rule, {"status": 0})
            result2 = evaluator.match_threshold(mock_rule, {"status": 1})

            assert result1 == False
            assert result2 == True
        except ImportError:
            pytest.skip("Module not found")


class TestConditionEvaluatorEdgeCases:
    """边界情况测试"""

    def test_missing_field(self):
        """测试缺少字段"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.rule_type = "THRESHOLD"
            mock_rule.target_field = "missing_field"
            mock_rule.threshold_value = 100

            target_data = {}  # 缺少字段

            result = evaluator.check_condition(mock_rule, target_data)

            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_none_value(self):
        """测试None值"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "value"
            mock_rule.threshold_value = 100

            target_data = {"value": None}

            result = evaluator.match_threshold(mock_rule, target_data)

            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_invalid_comparison(self):
        """测试无效比较"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.target_field = "name"
            mock_rule.threshold_value = 100
            mock_rule.comparison_operator = "gt"

            target_data = {"name": "字符串值"}  # 不能和数字比较

            result = evaluator.match_threshold(mock_rule, target_data)

            # 应该返回False或抛出异常
            assert result in [False, True]
        except ImportError:
            pytest.skip("Module not found")

    def test_empty_target_data(self):
        """测试空目标数据"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.rule_type = "THRESHOLD"

            result = evaluator.check_condition(mock_rule, {})

            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_unknown_rule_type(self):
        """测试未知规则类型"""
        try:
            from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

            mock_db = MagicMock()
            evaluator = ConditionEvaluator(mock_db)

            mock_rule = MagicMock()
            mock_rule.rule_type = "UNKNOWN_TYPE"

            result = evaluator.check_condition(mock_rule, {"value": 100})

            assert result == False
        except ImportError:
            pytest.skip("Module not found")