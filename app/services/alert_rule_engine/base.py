# -*- coding: utf-8 -*-
"""
预警规则引擎 - 基础配置和工具方法
"""

from typing import Any, Dict, Optional

from app.models.enums import AlertLevelEnum


class AlertRuleEngineBase:
    """预警规则引擎基类 - 包含配置和工具方法"""

    # 预警级别优先级（用于比较）
    LEVEL_PRIORITY = {
        AlertLevelEnum.INFO.value: 1,
        AlertLevelEnum.WARNING.value: 2,
        AlertLevelEnum.CRITICAL.value: 3,
        AlertLevelEnum.URGENT.value: 4,
    }

    # 响应时限（小时）
    RESPONSE_TIMEOUT = {
        AlertLevelEnum.INFO.value: 24,
        AlertLevelEnum.WARNING.value: 8,
        AlertLevelEnum.CRITICAL.value: 4,
        AlertLevelEnum.URGENT.value: 1,
    }

    def level_priority(self, level: str) -> int:
        """
        获取预警级别优先级

        Args:
            level: 预警级别

        Returns:
            int: 优先级（数字越大优先级越高）
        """
        return self.LEVEL_PRIORITY.get(level, 0)

    def get_field_value(
        self,
        field_path: str,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        获取字段值（支持点号分隔的嵌套路径）

        Args:
            field_path: 字段路径，如 'project.progress' 或 'days_delay'
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            字段值
        """
        # 先在 target_data 中查找
        value = self._get_nested_value(field_path, target_data)
        if value is not None:
            return value

        # 再在 context 中查找
        if context:
            value = self._get_nested_value(field_path, context)
            if value is not None:
                return value

        return None

    def _get_nested_value(self, field_path: str, data: Dict[str, Any]) -> Any:
        """获取嵌套字段值"""
        parts = field_path.split('.')
        value = data
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
