# -*- coding: utf-8 -*-
"""
JSON 安全解析工具函数

提供安全的 JSON 解析能力，避免因数据格式问题导致程序崩溃
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def safe_json_loads(
    value: Any,
    default: Optional[Any] = None,
    field_name: str = "unknown",
    log_error: bool = True,
) -> Any:
    """
    安全解析 JSON 字符串，失败时返回默认值

    Args:
        value: 需要解析的值（可能是 JSON 字符串、list、dict 或其他）
        default: 解析失败时返回的默认值
        field_name: 字段名称，用于日志记录
        log_error: 是否记录错误日志

    Returns:
        解析后的数据结构，或默认值

    Examples:
        >>> safe_json_loads('[1, 2, 3]', default=[])
        [1, 2, 3]
        >>> safe_json_loads('invalid', default=[])
        []
        >>> safe_json_loads(None, default={})
        {}
        >>> safe_json_loads({'key': 'value'}, default={})  # 已是 dict，直接返回
        {'key': 'value'}
    """
    # 处理 None 或空字符串
    if value is None:
        return default

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default

        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            if log_error:
                logger.warning(
                    "JSON 解析失败，字段: %s，值预览: %s，错误: %s",
                    field_name,
                    stripped[:100] if len(stripped) > 100 else stripped,
                    str(e),
                )
            return default

    # 已经是 list 或 dict，直接返回
    if isinstance(value, (list, dict)):
        return value

    # 其他类型（如 int、float），返回默认值
    if log_error:
        logger.warning(
            "JSON 解析跳过，字段: %s，不支持的类型: %s",
            field_name,
            type(value).__name__,
        )
    return default
