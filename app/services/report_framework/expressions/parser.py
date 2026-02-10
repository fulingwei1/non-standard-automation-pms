# -*- coding: utf-8 -*-
"""
表达式解析器

基于 Jinja2 的表达式引擎
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict

try:
    from jinja2 import Environment, BaseLoader, TemplateSyntaxError, UndefinedError
except ImportError:  # pragma: no cover - 可选依赖
    Environment = None
    BaseLoader = None
    TemplateSyntaxError = Exception
    UndefinedError = Exception

from app.services.report_framework.expressions.filters import register_filters


class ExpressionError(Exception):
    """表达式错误"""
    pass


class ExpressionParser:
    """
    表达式解析器

    使用 Jinja2 模板引擎解析和计算表达式
    """

    def __init__(self):
        """初始化表达式解析器"""
        self._env = self._create_environment()

    def _create_environment(self):
        """
        创建 Jinja2 环境

        Returns:
            配置好的 Jinja2 环境
        """
        if Environment is None or BaseLoader is None:
            return None

        env = Environment(
            loader=BaseLoader(),
            autoescape=False,
        )

        # 注册自定义过滤器
        register_filters(env)

        # 添加全局函数
        env.globals.update(self._get_global_functions())

        return env

    def _get_global_functions(self) -> Dict[str, Any]:
        """
        获取全局函数

        Returns:
            全局函数字典
        """
        return {
            # 日期函数
            "today": date.today,
            "now": datetime.now,
            "date": date,
            "datetime": datetime,
            "timedelta": timedelta,
            # 工具函数
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            # 日期快捷方式
            "last_monday": self._last_monday,
            "last_sunday": self._last_sunday,
            "this_month_start": self._this_month_start,
            "this_month_end": self._this_month_end,
            "last_month_start": self._last_month_start,
            "last_month_end": self._last_month_end,
        }

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        计算表达式

        Args:
            expression: Jinja2 表达式（如 "{{ tasks | length }}"）
            context: 上下文变量

        Returns:
            计算结果

        Raises:
            ExpressionError: 表达式语法错误或计算错误
        """
        # 如果不是表达式格式，直接返回
        if not expression or "{{" not in expression:
            return expression

        if self._env is None:
            raise ExpressionError("未安装 jinja2 依赖，无法计算表达式")

        try:
            template = self._env.from_string(expression)
            result = template.render(**context)

            # 尝试转换为数值
            return self._convert_result(result)

        except TemplateSyntaxError as e:
            raise ExpressionError(f"Invalid expression syntax: {e}")
        except UndefinedError as e:
            raise ExpressionError(f"Undefined variable in expression: {e}")
        except Exception as e:
            raise ExpressionError(f"Expression evaluation failed: {e}")

    def evaluate_dict(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归计算字典中的所有表达式

        Args:
            data: 包含表达式的字典
            context: 上下文变量

        Returns:
            计算后的字典
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.evaluate(value, context)
            elif isinstance(value, dict):
                result[key] = self.evaluate_dict(value, context)
            elif isinstance(value, list):
                result[key] = self.evaluate_list(value, context)
            else:
                result[key] = value
        return result

    def evaluate_list(self, data: list, context: Dict[str, Any]) -> list:
        """
        递归计算列表中的所有表达式

        Args:
            data: 包含表达式的列表
            context: 上下文变量

        Returns:
            计算后的列表
        """
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.evaluate(item, context))
            elif isinstance(item, dict):
                result.append(self.evaluate_dict(item, context))
            elif isinstance(item, list):
                result.append(self.evaluate_list(item, context))
            else:
                result.append(item)
        return result

    def _convert_result(self, result: str) -> Any:
        """
        尝试将结果转换为适当的类型

        Args:
            result: 字符串结果

        Returns:
            转换后的值
        """
        result = result.strip()

        # 尝试转换为整数
        try:
            return int(result)
        except ValueError:
            pass

        # 尝试转换为浮点数
        try:
            return float(result)
        except ValueError:
            pass

        # 布尔值
        if result.lower() == "true":
            return True
        if result.lower() == "false":
            return False

        # 保持字符串
        return result

    # === 日期快捷函数 ===

    @staticmethod
    def _last_monday() -> date:
        """上周一"""
        today = date.today()
        days_since_monday = today.weekday()
        if days_since_monday == 0:  # 今天是周一
            days_since_monday = 7
        return today - timedelta(days=days_since_monday)

    @staticmethod
    def _last_sunday() -> date:
        """上周日"""
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        if days_since_sunday == 0:  # 今天是周日
            days_since_sunday = 7
        return today - timedelta(days=days_since_sunday)

    @staticmethod
    def _this_month_start() -> date:
        """本月第一天"""
        today = date.today()
        return today.replace(day=1)

    @staticmethod
    def _this_month_end() -> date:
        """本月最后一天"""
        today = date.today()
        if today.month == 12:
            return today.replace(month=12, day=31)
        return today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    @staticmethod
    def _last_month_start() -> date:
        """上月第一天"""
        today = date.today()
        if today.month == 1:
            return today.replace(year=today.year - 1, month=12, day=1)
        return today.replace(month=today.month - 1, day=1)

    @staticmethod
    def _last_month_end() -> date:
        """上月最后一天"""
        today = date.today()
        return today.replace(day=1) - timedelta(days=1)
