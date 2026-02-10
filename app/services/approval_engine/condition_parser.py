# -*- coding: utf-8 -*-
"""
统一条件表达式解析器

支持三种语法：
1. Jinja2模板语法：{{ variable | filter }}
2. 简单条件语言：{"operator": "AND", "items": [...]}
3. 类SQL表达式：field > value AND field2 < value2
"""

import logging
import re
try:
    from jinja2 import Environment, TemplateSyntaxError, StrictUndefined
except ImportError:  # pragma: no cover - 可选依赖
    Environment = None
    TemplateSyntaxError = Exception
    StrictUndefined = None
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConditionParseError(Exception):
    """条件表达式解析错误"""

    pass


class ConditionEvaluator:
    """
    统一条件表达式评估器

    支持三种语法：
    1. Jinja2模板表达式
    2. 简单条件JSON（兼容现有格式）
    3. SQL-like表达式
    """

    def __init__(self):
        self._jinja_env = None
        if Environment is not None:
            self._jinja_env = Environment(
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
                autoescape=False,  # 条件表达式不需要HTML转义
            )

            # 注册自定义过滤器
            self._register_filters()

    def _register_filters(self):
        """注册Jinja2过滤器"""

        def length_filter(value):
            """计算长度"""
            if value is None:
                return 0
            return len(value)

        def sum_by_filter(items, field):
            """按字段求和"""
            if not items:
                return 0
            return sum(item.get(field, 0) for item in items if item)

        def count_by_filter(items, field, value=None):
            """按字段计数"""
            if not items:
                return 0
            if value is None:
                return len(items)
            return len([item for item in items if item.get(field) == value])

        def percentage_filter(value, decimals=1):
            """转百分比"""
            if value is None:
                return 0
            try:
                return round(float(value), decimals)
            except (TypeError, ValueError):
                return 0

        def default_filter(value, default_value):
            """默认值"""
            return value if value is not None else default_value

        # 使用正确的 Jinja2 API 注册过滤器
        self._jinja_env.filters["length"] = length_filter
        self._jinja_env.filters["sum_by"] = sum_by_filter
        self._jinja_env.filters["count_by"] = count_by_filter
        self._jinja_env.filters["percentage"] = percentage_filter
        self._jinja_env.filters["default"] = default_filter

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        评估表达式

        Args:
            expression: 表达式字符串
            context: 上下文数据

        Returns:
            评估结果

        Raises:
            ConditionParseError: 表达式语法错误
        """
        if not expression:
            return None

        # 检测表达式类型
        if "{{" in expression or "{%" in expression:
            # Jinja2模板语法
            return self._evaluate_jinja2(expression, context)
        elif expression.startswith("{") and expression.endswith("}"):
            # 简单条件JSON
            try:
                import json

                condition_dict = json.loads(expression)
                return self._evaluate_simple_conditions(condition_dict, context)
            except json.JSONDecodeError as e:
                raise ConditionParseError(f"JSON格式错误: {e}")
        else:
            # SQL-like表达式
            return self._evaluate_sql_like(expression, context)

    def _evaluate_jinja2(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        评估Jinja2模板表达式

        支持的语法示例：
        - {{ variable }}
        - {{ items | length }}
        - {{ items | sum_by("amount") }}
        - {{ value | percentage(1) }}
        - {{ today() }}  # 如果注册了today函数
        - {{ items | count_by("status", "DONE") }}
        """
        if self._jinja_env is None:
            raise ConditionParseError("未安装 jinja2 依赖，无法解析模板表达式")

        try:
            template = self._jinja_env.from_string(expression)
            result = template.render(**context)
            # 尝试转换为数值类型
            try:
                # 尝试转换为整数
                if "." in result:
                    return float(result)
                return int(result)
            except (ValueError, TypeError):
                # 返回字符串
                return result
        except TemplateSyntaxError as e:
            raise ConditionParseError(f"Jinja2语法错误: {e}")
        except Exception as e:
            logger.error(f"Jinja2表达式评估失败: {e}")
            raise ConditionParseError(f"表达式评估失败: {e}")

    def _evaluate_simple_conditions(
        self, conditions: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """
        评估简单条件JSON（兼容现有格式）

        格式示例：
        {
            "operator": "AND",  // AND/OR
            "items": [
                {"field": "form.leave_days", "op": "<=", "value": 3},
                {"field": "entity.gross_margin", "op": ">=", "value": 0.2}
            ]
        }
        """
        if not conditions or not isinstance(conditions, dict):
            return True

        operator = conditions.get("operator", "AND")
        items = conditions.get("items", [])

        if not items:
            return True

        results = [self._evaluate_single_condition(item, context) for item in items]

        if operator == "AND":
            return all(results)
        elif operator == "OR":
            return any(results)
        else:
            # 默认AND
            return all(results)

    def _evaluate_single_condition(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """
        评估单个简单条件
        """
        field = condition.get("field", "")
        op = condition.get("op", "==")
        expected = condition.get("value")

        # 获取字段值
        actual = self._get_field_value(field, context)

        # 比较
        return self._compare_values(actual, op, expected)

    def _get_field_value(self, field_path: str, context: Dict[str, Any]) -> Any:
        """
        获取字段值，支持嵌套路径

        支持的路径前缀：
        - form.xxx: 表单字段
        - entity.xxx: 业务实体属性
        - initiator.xxx: 发起人属性
        - sys.xxx: 系统变量
        - user.xxx: 当前用户
        - today(): 系统日期函数
        """
        if not field_path:
            return None

        # 特殊处理系统函数
        if field_path == "today()" or field_path == "now()":
            from datetime import datetime

            return datetime.now().date() if "today" in field_path else datetime.now()

        # 特殊处理用户上下文
        if field_path.startswith("user."):
            user = context.get("user", {})
            if isinstance(user, dict):
                return self._get_nested_value(user, field_path[5:])
            elif hasattr(user, field_path[5:]):
                return getattr(user, field_path[5:])
            return None

        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """获取嵌套对象值"""
        if not path:
            return obj

        parts = path.split(".")
        value = obj
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
            if value is None:
                return None
        return value

    def _compare_values(self, actual: Any, op: str, expected: Any) -> bool:
        """
        比较两个值

        支持的操作符：
        - ==, !=: 相等/不等
        - >, >=, <, <=: 数值比较
        - in, not_in: 列表包含
        - between: 区间（闭区间）
        - contains: 字符串包含
        - starts_with, ends_with: 字符串前缀/后缀
        - is_null: 空值判断
        - regex: 正则匹配
        - and, or: 逻辑运算
        """
        try:
            if op == "==" or op == "=":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == ">":
                return actual is not None and actual > expected
            elif op == ">=":
                return actual is not None and actual >= expected
            elif op == "<":
                return actual is not None and actual < expected
            elif op == "<=":
                return actual is not None and actual <= expected
            elif op == "in":
                return actual in (expected if expected else [])
            elif op == "not_in":
                return actual not in (expected if expected else [])
            elif op == "between":
                if (
                    actual is None
                    or not isinstance(expected, (list, tuple))
                    or len(expected) != 2
                ):
                    return False
                return expected[0] <= actual <= expected[1]
            elif op == "contains":
                return expected in str(actual) if actual is not None else False
            elif op == "starts_with":
                return (
                    str(actual).startswith(str(expected))
                    if actual is not None
                    else False
                )
            elif op == "ends_with":
                return (
                    str(actual).endswith(str(expected)) if actual is not None else False
                )
            elif op == "is_null":
                return (actual is None) == expected
            elif op == "regex":
                import re

                return (
                    bool(re.match(expected, str(actual)))
                    if actual is not None
                    else False
                )
            elif op == "and":
                if isinstance(expected, (list, tuple)) and len(expected) == 2:
                    return self._compare_values(actual, expected[0], expected[1])
                return False
            elif op == "or":
                if isinstance(expected, (list, tuple)) and len(expected) == 2:
                    return self._compare_values(actual, expected[0], expected[1])
                return False
            else:
                logger.warning(f"不支持的操作符: {op}")
                return False
        except (TypeError, ValueError, AttributeError) as e:
            logger.error(f"比较操作失败: {e}")
            return False

    def _evaluate_sql_like(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        评估SQL-like表达式

        支持的语法：
        - field > value
        - field >= value AND field2 < value2
        - field IN (v1, v2, v3)
        - field BETWEEN min AND max

        将SQL-like转换为简单条件JSON格式
        """
        if not expression:
            return True

        try:
            return self._parse_sql_expression(expression, context)
        except Exception as e:
            logger.error(f"SQL-like表达式解析失败: {e}")
            # 降级到直接评估
            return self._evaluate_jinja2(f"{{{{{expression}}}}}", context)

    def _parse_sql_expression(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        解析SQL-like表达式

        将表达式转换为简单条件JSON格式
        """
        # 标准化：去除多余空格，统一关键字大小写
        expr = expression.strip().replace("\n", " ")

        # 使用正则表达式分割逻辑运算符
        # 支持的运算符：AND, OR
        and_parts = self._split_by_operator(expr, "AND", "and")
        or_parts = self._split_by_operator(expr, "OR", "or")

        if and_parts:
            # AND逻辑
            items = [
                self._parse_sql_condition(part.strip(), context) for part in and_parts
            ]
            return all(items)
        elif or_parts:
            # OR逻辑
            items = [
                self._parse_sql_condition(part.strip(), context) for part in or_parts
            ]
            return any(items)
        else:
            # 单个条件
            return self._parse_sql_condition(expr, context)

    def _split_by_operator(self, expr: str, op1: str, op2: str) -> List[str]:
        """按逻辑运算符分割表达式"""
        # 使用正则匹配，避免在字符串中误判
        pattern = rf"\b(?:{op1}|{op2})\b"
        return re.split(pattern, expr, flags=re.IGNORECASE)

    def _parse_sql_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        解析单个SQL条件

        支持：
        - field > value
        - field >= value
        - field < value
        - field <= value
        - field == value
        - field != value
        - field IN (v1, v2)
        - field BETWEEN min AND max
        - field IS NULL
        - field IS NOT NULL
        """
        condition = condition.strip()

        # 处理 IS NULL / IS NOT NULL
        if " IS NOT NULL" in condition.upper():
            field = condition.replace(" IS NOT NULL", "").strip()
            actual = self._get_field_value(field, context)
            return actual is not None
        elif " IS NULL" in condition.upper():
            field = condition.replace(" IS NULL", "").strip()
            actual = self._get_field_value(field, context)
            return actual is None

        # 处理 IN
        in_match = re.match(r"(.+?)\s+IN\s*\((.*?)\)", condition, re.IGNORECASE)
        if in_match:
            field = in_match.group(1).strip()
            values_str = in_match.group(2).strip()
            # 解析值列表
            values = [v.strip() for v in values_str.split(",")]
            actual = self._get_field_value(field, context)
            try:
                return actual in values
            except TypeError:
                return str(actual) in values

        # 处理 BETWEEN
        between_match = re.match(
            r"(.+?)\s+BETWEEN\s+(.+?)\s+AND\s+(.+)", condition, re.IGNORECASE
        )
        if between_match:
            field = between_match.group(1).strip()
            min_val = self._parse_value(between_match.group(2).strip())
            max_val = self._parse_value(between_match.group(3).strip())
            actual = self._get_field_value(field, context)
            try:
                return min_val <= actual <= max_val
            except TypeError:
                return False

        # 处理比较运算符
        operators = [
            (r">=", ">="),
            (r"<=", "<="),
            (r"=", "!="),
            (r">", ">"),
            (r"<", "<"),
            (r"=", "=="),
        ]

        for op_pattern, op_name in operators:
            # 使用正则查找运算符
            op_regex = re.escape(op_pattern)
            match = re.match(rf"(.+?)\s*{op_regex}\s*(.+)", condition, re.IGNORECASE)
            if match:
                field = match.group(1).strip()
                value = self._parse_value(match.group(2).strip())
                actual = self._get_field_value(field, context)
                return self._compare_values(actual, op_name, value)

        # 无法解析，直接返回False
        logger.warning(f"无法解析条件: {condition}")
        return False

    def _parse_value(self, value_str: str) -> Any:
        """
        解析值字符串

        支持的格式：
        - 数字：123, 45.67
        - 字符串：'text', "text"
        - 布尔：true, false
        """
        value_str = value_str.strip()

        # 布尔值
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"

        # 尝试解析为数字
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # 去除引号
        if (value_str.startswith("'") and value_str.endswith("'")) or (
            value_str.startswith('"') and value_str.endswith('"')
        ):
            return value_str[1:-1]

        return value_str
