# -*- coding: utf-8 -*-
"""
Decimal 工具函数

提供安全的 Decimal 类型转换和计算工具，避免在各服务中重复实现相同的转换逻辑。
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict


def parse_decimal(value: Any, default: str = "0") -> Decimal:
    """
    将任意值安全转换为 Decimal。

    处理各种输入类型（int, float, str, Decimal, None），
    转换失败时返回默认值。

    Args:
        value: 要转换的值，支持 int/float/str/Decimal/None
        default: 转换失败时的默认值（字符串形式）

    Returns:
        转换后的 Decimal 值

    Examples:
        >>> parse_decimal("123.45")
        Decimal('123.45')
        >>> parse_decimal(None)
        Decimal('0')
        >>> parse_decimal("invalid", default="100")
        Decimal('100')
    """
    if value is None or value == "":
        return Decimal(default)

    # 如果已经是 Decimal，直接返回
    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def decimal_from_percentage(
    percentage: Any,
    base: Decimal,
    places: int = 2
) -> Decimal:
    """
    根据百分比计算实际金额。

    Args:
        percentage: 百分比值（如 25 表示 25%）
        base: 基准金额
        places: 小数位数，默认 2 位

    Returns:
        计算后的金额，已四舍五入

    Examples:
        >>> decimal_from_percentage(25, Decimal("1000"))
        Decimal('250.00')
        >>> decimal_from_percentage("30.5", Decimal("200"), places=4)
        Decimal('61.0000')
    """
    pct = parse_decimal(percentage, default="0")
    result = base * pct / Decimal("100")
    return quantize_decimal(result, places)


def safe_decimal_from_dict(
    data: Dict[str, Any],
    key: str,
    default: str = "0"
) -> Decimal:
    """
    从字典中安全提取并转换为 Decimal。

    Args:
        data: 源字典
        key: 要提取的键名
        default: 键不存在或值无效时的默认值

    Returns:
        转换后的 Decimal 值

    Examples:
        >>> safe_decimal_from_dict({"price": "99.9"}, "price")
        Decimal('99.9')
        >>> safe_decimal_from_dict({}, "price", default="100")
        Decimal('100')
    """
    value = data.get(key)
    return parse_decimal(value, default=default)


def quantize_decimal(value: Decimal, places: int = 2) -> Decimal:
    """
    将 Decimal 四舍五入到指定小数位。

    Args:
        value: 要处理的 Decimal 值
        places: 保留的小数位数，默认 2 位

    Returns:
        四舍五入后的 Decimal 值

    Examples:
        >>> quantize_decimal(Decimal("123.456"))
        Decimal('123.46')
        >>> quantize_decimal(Decimal("123.456"), places=1)
        Decimal('123.5')
    """
    if not isinstance(value, Decimal):
        value = parse_decimal(value)

    # 构建量化模板：如 places=2 -> "0.01"
    quantize_str = "0." + "0" * places if places > 0 else "1"
    return value.quantize(Decimal(quantize_str))


def ensure_decimal(value: Any) -> Decimal:
    """
    确保值为 Decimal 类型，用于类型注解和运行时转换。

    与 parse_decimal 的区别：此函数在转换失败时会抛出异常，
    适用于必须有有效数值的场景。

    Args:
        value: 要转换的值

    Returns:
        转换后的 Decimal 值

    Raises:
        ValueError: 当值无法转换为有效 Decimal 时
    """
    if value is None or value == "":
        raise ValueError("值不能为空")

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError(f"无法转换为 Decimal: {value}") from e


def sum_decimals(*values: Any, default: str = "0") -> Decimal:
    """
    安全地求和多个数值。

    Args:
        *values: 要求和的数值列表
        default: 无效值的默认值

    Returns:
        求和结果

    Examples:
        >>> sum_decimals("10", 20, Decimal("30.5"))
        Decimal('60.5')
    """
    return sum(parse_decimal(v, default) for v in values)


# 常用的 Decimal 常量，避免重复创建
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
