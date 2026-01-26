# -*- coding: utf-8 -*-
"""
条件表达式解析器单元测试

测试范围：
1. Jinja2模板语法
2. 简单条件JSON
3. SQL-like表达式
4. 各类比较操作符
5. 复杂嵌套条件
"""

import pytest
from app.services.approval_engine.condition_parser import (
    ConditionEvaluator,
    ConditionParseError,
)


class TestConditionEvaluator:
    """条件表达式解析器测试类"""

    def setup_method(self):
        """每个测试前创建一个新的解析器实例"""
        self.parser = ConditionEvaluator()

    # ============ Jinja2模板语法测试 ============

    def test_jinja2_simple_variable(self):
        """测试简单变量替换"""
        context = {
            "user": {"name": "张三"},
            "entity": {"amount": 1000},
        }
        result = self.parser.evaluate("{{ user.name }}", context)
        assert result == "张三"

    def test_jinja2_nested_field(self):
        """测试嵌套字段访问"""
        context = {
            "form": {"leave_days": 3},
            "initiator": {"dept_name": "技术部"},
            "entity": {"project": {"id": 1, "title": "测试项目"}},
        }

        result = self.parser.evaluate("{{ form.leave_days }} 天", context)
        assert result == "3 天"

    def test_jinja2_length_filter(self):
        """测试length过滤器"""
        context = {
            "items": [1, 2, 3, 4, 5],
            "tasks": [
                {"id": 1, "status": "DONE"},
                {"id": 2, "status": "DONE"},
                {"id": 3, "status": "PENDING"},
            ],
        }
        result = self.parser.evaluate("{{ items | length }}", context)
        assert result == 5

    def test_jinja2_sum_by_filter(self):
        """测试sum_by过滤器"""
        context = {
            "items": [
                {"amount": 100},
                {"amount": 200},
                {"amount": 150},
            ],
        }
        result = self.parser.evaluate('{{ items | sum_by("amount") }}', context)
        assert result == 450

    def test_jinja2_count_by_filter(self):
        """测试count_by过滤器"""
        context = {
            "tasks": [
                {"id": 1, "status": "DONE"},
                {"id": 2, "status": "DONE"},
                {"id": 3, "status": "PENDING"},
            ],
        }
        result = self.parser.evaluate(
            '{{ tasks | count_by("status", "DONE") }}', context
        )
        assert result == 2

    def test_jinja2_percentage_filter(self):
        """测试percentage过滤器"""
        context = {
            "value": 85.5,
            "decimals": 1,
        }
        result = self.parser.evaluate("{{ value | percentage(1) }}", context)
        assert result == 85.5

    def test_jinja2_default_filter(self):
        """测试default过滤器"""
        context = {"value": None}
        result = self.parser.evaluate("{{ value | default(0) }}", context)
        assert result == 0

    # ============ 简单条件JSON测试 ============

    def test_simple_condition_eq(self):
        """测试相等条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": "==", "value": 1000},
            ],
        }
        context = {"form": {"amount": 1000}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_ne(self):
        """测试不等条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.type", "op": "!=", "value": "LEAVE"},
            ],
        }
        context = {"form": {"type": "LEAVE"}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_gt(self):
        """测试大于条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">", "value": 500},
            ],
        }
        context = {"form": {"amount": 1000}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_gte(self):
        """测试大于等于条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000},
            ],
        }
        context = {"form": {"amount": 1000}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_lt(self):
        """测试小于条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": "<", "value": 1000},
            ],
        }
        context = {"form": {"amount": 1000}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_lte(self):
        """测试小于等于条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": "<=", "value": 1000},
            ],
        }
        context = {"form": {"amount": 1000}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_in(self):
        """测试IN条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.dept_id", "op": "in", "value": [1, 2, 3]},
            ],
        }
        context = {"form": {"dept_id": 2}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_not_in(self):
        """测试NOT IN条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.dept_id", "op": "not_in", "value": [1, 2, 3]},
            ],
        }
        context = {"form": {"dept_id": 4}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_between(self):
        """测试BETWEEN条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": "between", "value": [500, 1000]},
            ],
        }
        context = {"form": {"amount": 700}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_contains(self):
        """测试CONTAINS条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "entity.project_name", "op": "contains", "value": "测试"},
            ],
        }
        context = {"entity": {"project_name": "这是测试项目"}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_starts_with(self):
        """测试STARTS_WITH条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "entity.project_code", "op": "starts_with", "value": "PJ"},
            ],
        }
        context = {"entity": {"project_code": "PJ250101"}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_ends_with(self):
        """测试ENDS_WITH条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "entity.project_code", "op": "ends_with", "value": "101"},
            ],
        }
        context = {"entity": {"project_code": "PJ250101"}}
        result = self.parser.evaluate(conditions, conditions, context)
        assert result is True

    def test_simple_condition_regex(self):
        """测试正则匹配条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {
                    "field": "form.email",
                    "op": "regex",
                    "value": r"^[a-z]+@[a-z]+\.com$",
                },
            ],
        }
        context = {"form": {"email": "test@example.com"}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_simple_condition_is_null(self):
        """测试IS NULL条件"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.attachment", "op": "is_null", "value": False},
            ],
        }
        context = {"form": {"attachment": None}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_complex_condition_or_operator(self):
        """测试OR操作符"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">", "value": 500},
                {"field": "form.type", "op": "==", "value": "LEAVE"},
            ],
        }
        context = {"form": {"amount": 1000, "type": "LEAVE"}}
        result = self.parser.evaluate(conditions, context)
        assert result is True

    def test_nested_field_path(self):
        """测试嵌套字段路径"""
        context = {
            "entity": {
                "project": {
                    "customer": {
                        "name": "测试客户",
                    },
                    "contract": {
                        "amount": 50000,
                    },
                }
            },
        }

        result = self.parser.evaluate("{{ entity.project.customer.name }}", context)
        assert result == "测试客户"

    def test_user_context(self):
        """测试用户上下文"""
        context = {
            "user": {"id": 1, "name": "测试用户", "role": "manager"},
        }

        result = self.parser.evaluate("{{ user.id }}", context)
        assert result == 1

        # ============ SQL-like表达式测试 ============

    def test_sql_like_field_comparison(self):
        """测试SQL-like字段比较"""
        expression = "entity.amount > 50000"
        context = {"entity": {"amount": 60000}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_and_condition(self):
        """测试AND逻辑"""
        expression = 'entity.amount > 50000 AND entity.status == "ACTIVE"'
        context = {"entity": {"amount": 60000, "status": "ACTIVE"}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_or_condition(self):
        """测试OR逻辑"""
        expression = "entity.amount > 100000 OR entity.amount < 10000"
        context = {"entity": {"amount": 60000}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_in_operator(self):
        """测试IN操作符"""
        expression = "entity.department_id IN (1, 2, 3)"
        context = {"entity": {"department_id": 2}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_between_operator(self):
        """测试BETWEEN操作符"""
        expression = "entity.amount BETWEEN 10000 AND 50000"
        context = {"entity": {"amount": 25000}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_is_null(self):
        """测试IS NULL操作符"""
        expression = "entity.approved_at IS NULL"
        context = {"entity": {"approved_at": None}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_is_not_null(self):
        """测试IS NOT NULL操作符"""
        expression = "entity.approved_at IS NOT NULL"
        context = {"entity": {"approved_at": None}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    def test_sql_like_complex(self):
        """测试复杂SQL-like表达式"""
        expression = (
            'entity.amount > 100000 AND entity.status IN ("APPROVED", "COMPLETED")'
        )
        context = {"entity": {"amount": 60000, "status": "COMPLETED"}}
        result = self.parser.evaluate(expression, context)
        assert result is True

    # ============ 错误处理测试 ============

    def test_invalid_jinja2_expression(self):
        """测试无效的Jinja2表达式"""
        with pytest.raises(ConditionParseError):
            self.parser.evaluate("{{{ invalid syntax }", {})

    def test_invalid_simple_condition_json(self):
        """测试无效的条件JSON"""
        with pytest.raises(ConditionParseError):
            self.parser.evaluate({"operator": "INVALID", "items": []}, {})

    def test_invalid_sql_like_expression(self):
        """测试无效的SQL-like表达式"""
        with pytest.raises(ConditionParseError):
            self.parser.evaluate("field > value AND", {})

    # ============ 边界情况测试 ============

    def test_null_value_comparison(self):
        """测试空值比较"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.attachment", "op": "==", "value": None},
            ],
        }
        context = {"form": {"attachment": None}}
        result = self.parser.evaluate(conditions, context)
        # 空值等于空值，应该返回False
        assert result is False

    def test_empty_conditions(self):
        """测试空条件列表"""
        conditions = {"operator": "AND", "items": []}
        result = self.parser.evaluate(conditions, context)
        # 空条件列表应该返回True
        assert result is True

    def test_boolean_values(self):
        """测试布尔值比较"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.is_approved", "op": "==", "value": True},
                {"field": "form.is_active", "op": "==", "value": False},
            ],
        }
        context = {"form": {"is_approved": True, "is_active": False}}
        result = self.parser.evaluate(conditions, context)
        assert result is False  # 一个True，一个False

    def test_numeric_comparison(self):
        """测试数值比较"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.discount_rate", "op": ">=", "value": 0.1},
                {"field": "form.quantity", "op": ">=", "value": 0},
                {"field": "form.unit_price", "op": ">=", "value": 0},
            ],
        }
        context = {
            "form": {"discount_rate": 0.15, "quantity": 10, "unit_price": 100},
        }
        result = self.parser.evaluate(conditions, context)
        assert result is True
