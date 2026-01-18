# -*- coding: utf-8 -*-
"""
预警规则引擎单元测试

重点测试 match_custom_expr 方法的安全表达式评估功能
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.alert_rule_engine import AlertRuleEngine


class TestAlertRuleEngineCustomExpr:
    """测试预警规则引擎的自定义表达式匹配功能"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def engine(self, mock_db):
        """创建预警规则引擎实例"""
        with patch.object(AlertRuleEngine, '__init__', lambda x, y: None):
            engine = AlertRuleEngine.__new__(AlertRuleEngine)
            engine.db = mock_db
            return engine

    @pytest.fixture
    def mock_rule(self):
        """创建模拟规则"""
        rule = MagicMock()
        rule.rule_code = "TEST001"
        rule.condition_expr = None
        return rule

    # --- 基本表达式测试 ---

    def test_empty_expression_returns_false(self, engine, mock_rule):
        """测试空表达式返回 False"""
        mock_rule.condition_expr = None
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

        mock_rule.condition_expr = ""
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

    def test_simple_comparison_greater_than(self, engine, mock_rule):
        """测试简单比较表达式 - 大于"""
        mock_rule.condition_expr = "progress > 50"

        # 满足条件
        result = engine.match_custom_expr(mock_rule, {"progress": 80})
        assert result is True

        # 不满足条件
        result = engine.match_custom_expr(mock_rule, {"progress": 30})
        assert result is False

    def test_simple_comparison_less_than(self, engine, mock_rule):
        """测试简单比较表达式 - 小于"""
        mock_rule.condition_expr = "days_delay < 5"

        result = engine.match_custom_expr(mock_rule, {"days_delay": 3})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"days_delay": 10})
        assert result is False

    def test_equality_comparison(self, engine, mock_rule):
        """测试相等比较表达式"""
        mock_rule.condition_expr = "status == 'DELAYED'"

        result = engine.match_custom_expr(mock_rule, {"status": "DELAYED"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"status": "NORMAL"})
        assert result is False

    def test_inequality_comparison(self, engine, mock_rule):
        """测试不等比较表达式"""
        mock_rule.condition_expr = "health_level != 'H1'"

        result = engine.match_custom_expr(mock_rule, {"health_level": "H2"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"health_level": "H1"})
        assert result is False

    # --- 复合表达式测试 ---

    def test_logical_and(self, engine, mock_rule):
        """测试逻辑与表达式"""
        mock_rule.condition_expr = "progress < 50 and days_delay > 5"

        # 两个条件都满足
        result = engine.match_custom_expr(mock_rule, {"progress": 30, "days_delay": 10})
        assert result is True

        # 只有一个条件满足
        result = engine.match_custom_expr(mock_rule, {"progress": 30, "days_delay": 2})
        assert result is False

        result = engine.match_custom_expr(mock_rule, {"progress": 80, "days_delay": 10})
        assert result is False

    def test_logical_or(self, engine, mock_rule):
        """测试逻辑或表达式"""
        mock_rule.condition_expr = "progress > 90 or cost_ratio > 1.2"

        # 第一个条件满足
        result = engine.match_custom_expr(mock_rule, {"progress": 95, "cost_ratio": 1.0})
        assert result is True

        # 第二个条件满足
        result = engine.match_custom_expr(mock_rule, {"progress": 50, "cost_ratio": 1.5})
        assert result is True

        # 都不满足
        result = engine.match_custom_expr(mock_rule, {"progress": 50, "cost_ratio": 1.0})
        assert result is False

    def test_complex_expression(self, engine, mock_rule):
        """测试复杂表达式"""
        mock_rule.condition_expr = "(progress < 50 and days_delay > 5) or health_level == 'H3'"

        # 满足第一组条件
        result = engine.match_custom_expr(mock_rule, {
            "progress": 30,
            "days_delay": 10,
            "health_level": "H1"
        })
        assert result is True

        # 满足第二个条件
        result = engine.match_custom_expr(mock_rule, {
            "progress": 80,
            "days_delay": 2,
            "health_level": "H3"
        })
        assert result is True

    # --- 算术运算测试 ---

    def test_arithmetic_expression(self, engine, mock_rule):
        """测试算术运算表达式"""
        mock_rule.condition_expr = "cost_actual > cost_budget * 1.1"

        result = engine.match_custom_expr(mock_rule, {
            "cost_actual": 12000,
            "cost_budget": 10000
        })
        assert result is True

        result = engine.match_custom_expr(mock_rule, {
            "cost_actual": 10500,
            "cost_budget": 10000
        })
        assert result is False

    def test_division_expression(self, engine, mock_rule):
        """测试除法运算表达式"""
        mock_rule.condition_expr = "completed_tasks / total_tasks < 0.5"

        result = engine.match_custom_expr(mock_rule, {
            "completed_tasks": 3,
            "total_tasks": 10
        })
        assert result is True

    # --- 内置函数测试 ---

    def test_abs_function(self, engine, mock_rule):
        """测试 abs 函数"""
        mock_rule.condition_expr = "abs(deviation) > 10"

        result = engine.match_custom_expr(mock_rule, {"deviation": -15})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"deviation": 5})
        assert result is False

    def test_len_function(self, engine, mock_rule):
        """测试 len 函数"""
        mock_rule.condition_expr = "len(pending_issues) > 3"

        result = engine.match_custom_expr(mock_rule, {
            "pending_issues": [1, 2, 3, 4, 5]
        })
        assert result is True

        result = engine.match_custom_expr(mock_rule, {
            "pending_issues": [1, 2]
        })
        assert result is False

    def test_min_max_functions(self, engine, mock_rule):
        """测试 min/max 函数"""
        mock_rule.condition_expr = "max(values) - min(values) > 100"

        result = engine.match_custom_expr(mock_rule, {
            "values": [50, 100, 200, 75]
        })
        assert result is True

        result = engine.match_custom_expr(mock_rule, {
            "values": [50, 100, 120]
        })
        assert result is False

    def test_sum_function(self, engine, mock_rule):
        """测试 sum 函数"""
        mock_rule.condition_expr = "sum(costs) > 10000"

        result = engine.match_custom_expr(mock_rule, {
            "costs": [3000, 4000, 5000]
        })
        assert result is True

    def test_round_function(self, engine, mock_rule):
        """测试 round 函数"""
        mock_rule.condition_expr = "round(percentage, 1) >= 85.5"

        result = engine.match_custom_expr(mock_rule, {"percentage": 85.567})
        assert result is True

    # --- 列表操作测试 ---

    def test_in_operator_with_list(self, engine, mock_rule):
        """测试 in 操作符与列表"""
        mock_rule.condition_expr = "health_level in ['H2', 'H3']"

        result = engine.match_custom_expr(mock_rule, {"health_level": "H2"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"health_level": "H3"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"health_level": "H1"})
        assert result is False

    def test_not_in_operator(self, engine, mock_rule):
        """测试 not in 操作符"""
        mock_rule.condition_expr = "status not in ['COMPLETED', 'CANCELLED']"

        result = engine.match_custom_expr(mock_rule, {"status": "IN_PROGRESS"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"status": "COMPLETED"})
        assert result is False

    # --- 上下文数据测试 ---

    def test_with_context_data(self, engine, mock_rule):
        """测试上下文数据合并"""
        mock_rule.condition_expr = "project_progress < threshold"

        target_data = {"project_progress": 40}
        context = {"threshold": 50}

        result = engine.match_custom_expr(mock_rule, target_data, context)
        assert result is True

    def test_context_overrides_target(self, engine, mock_rule):
        """测试上下文数据覆盖目标数据"""
        mock_rule.condition_expr = "value > 50"

        target_data = {"value": 30}
        context = {"value": 80}  # 上下文中的值会覆盖

        result = engine.match_custom_expr(mock_rule, target_data, context)
        assert result is True

    # --- 错误处理测试 ---

    def test_undefined_variable_returns_false(self, engine, mock_rule):
        """测试未定义变量返回 False"""
        mock_rule.condition_expr = "undefined_variable > 10"

        result = engine.match_custom_expr(mock_rule, {"progress": 50})
        assert result is False

    def test_syntax_error_returns_false(self, engine, mock_rule):
        """测试语法错误返回 False"""
        mock_rule.condition_expr = "progress > > 50"  # 语法错误

        result = engine.match_custom_expr(mock_rule, {"progress": 80})
        assert result is False

    def test_type_error_returns_false(self, engine, mock_rule):
        """测试类型错误返回 False"""
        mock_rule.condition_expr = "progress + 'string'"  # 类型不兼容

        result = engine.match_custom_expr(mock_rule, {"progress": 50})
        assert result is False

    # --- 安全性测试 ---

    def test_no_arbitrary_code_execution(self, engine, mock_rule):
        """测试不能执行任意代码"""
        # 尝试导入模块 - 应该失败并返回 False
        mock_rule.condition_expr = "__import__('os').system('echo hacked')"
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

    def test_no_builtin_access(self, engine, mock_rule):
        """测试不能访问危险的内置函数"""
        mock_rule.condition_expr = "eval('1+1')"
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

        mock_rule.condition_expr = "exec('print(1)')"
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

    def test_no_file_operations(self, engine, mock_rule):
        """测试不能执行文件操作"""
        mock_rule.condition_expr = "open('/etc/passwd').read()"
        result = engine.match_custom_expr(mock_rule, {})
        assert result is False

    # --- 边界情况测试 ---

    def test_boolean_result_conversion(self, engine, mock_rule):
        """测试非布尔值结果转换"""
        # 数字转布尔
        mock_rule.condition_expr = "count"
        result = engine.match_custom_expr(mock_rule, {"count": 5})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"count": 0})
        assert result is False

        # 字符串转布尔
        mock_rule.condition_expr = "name"
        result = engine.match_custom_expr(mock_rule, {"name": "test"})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"name": ""})
        assert result is False

    def test_none_value_handling(self, engine, mock_rule):
        """测试 None 值处理"""
        mock_rule.condition_expr = "value is None"

        result = engine.match_custom_expr(mock_rule, {"value": None})
        assert result is True

        result = engine.match_custom_expr(mock_rule, {"value": 0})
        assert result is False

    def test_float_precision(self, engine, mock_rule):
        """测试浮点数精度"""
        mock_rule.condition_expr = "abs(actual - expected) < 0.001"

        result = engine.match_custom_expr(mock_rule, {
            "actual": 0.1 + 0.2,
            "expected": 0.3
        })
        assert result is True
