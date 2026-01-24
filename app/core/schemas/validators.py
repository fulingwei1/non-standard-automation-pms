# -*- coding: utf-8 -*-
"""
统一验证器

提供通用的验证函数，用于数据验证和格式化。
所有验证器都应该抛出 ValueError 异常，包含清晰的错误消息。
"""

import re
from datetime import datetime, date
from typing import Any, Optional, Tuple
from decimal import Decimal, InvalidOperation


# ========== 项目相关验证 ==========

def validate_project_code(code: str) -> str:
    """
    验证项目编码格式
    
    格式：PJyymmddxxx（如 PJ250101001）
    - PJ: 固定前缀
    - yymmdd: 年月日（6位）
    - xxx: 序号（3位）
    
    Args:
        code: 项目编码
    
    Returns:
        str: 验证后的项目编码
    
    Raises:
        ValueError: 如果编码格式不正确
    """
    if not code:
        raise ValueError("项目编码不能为空")
    
    code = code.strip().upper()
    
    if not code.startswith("PJ"):
        raise ValueError("项目编码必须以PJ开头")
    
    if len(code) != 11:
        raise ValueError("项目编码长度必须为11位（格式：PJyymmddxxx）")
    
    # 验证日期部分
    date_part = code[2:8]
    try:
        year = 2000 + int(date_part[0:2])
        month = int(date_part[2:4])
        day = int(date_part[4:6])
        date(year, month, day)  # 验证日期有效性
    except (ValueError, IndexError):
        raise ValueError(f"项目编码中的日期部分无效：{date_part}")
    
    # 验证序号部分
    seq_part = code[8:11]
    if not seq_part.isdigit():
        raise ValueError("项目编码的序号部分必须是3位数字")
    
    return code


def validate_machine_code(code: str) -> str:
    """
    验证机台编码格式
    
    格式：PNxxx（如 PN001）
    
    Args:
        code: 机台编码
    
    Returns:
        str: 验证后的机台编码
    
    Raises:
        ValueError: 如果编码格式不正确
    """
    if not code:
        raise ValueError("机台编码不能为空")
    
    code = code.strip().upper()
    
    if not code.startswith("PN"):
        raise ValueError("机台编码必须以PN开头")
    
    if len(code) < 3:
        raise ValueError("机台编码长度至少为3位")
    
    return code


# ========== 联系方式验证 ==========

def validate_phone(phone: str) -> str:
    """
    验证手机号格式
    
    支持中国大陆手机号：1[3-9]xxxxxxxxx（11位）
    
    Args:
        phone: 手机号
    
    Returns:
        str: 验证后的手机号
    
    Raises:
        ValueError: 如果手机号格式不正确
    """
    if not phone:
        raise ValueError("手机号不能为空")
    
    phone = phone.strip().replace("-", "").replace(" ", "")
    
    # 中国大陆手机号：1[3-9]xxxxxxxxx
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        raise ValueError("手机号格式不正确，请输入11位中国大陆手机号")
    
    return phone


def validate_email(email: str) -> str:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        str: 验证后的邮箱地址
    
    Raises:
        ValueError: 如果邮箱格式不正确
    """
    if not email:
        raise ValueError("邮箱地址不能为空")
    
    email = email.strip().lower()
    
    # 基本邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("邮箱格式不正确")
    
    # 长度限制
    if len(email) > 254:
        raise ValueError("邮箱地址过长（最大254字符）")
    
    return email


def validate_phone_or_email(value: str) -> str:
    """
    验证手机号或邮箱
    
    自动识别是手机号还是邮箱
    
    Args:
        value: 手机号或邮箱
    
    Returns:
        str: 验证后的值
    
    Raises:
        ValueError: 如果既不是手机号也不是邮箱
    """
    if not value:
        raise ValueError("手机号或邮箱不能为空")
    
    value = value.strip()
    
    # 尝试作为邮箱验证
    if "@" in value:
        return validate_email(value)
    
    # 尝试作为手机号验证
    try:
        return validate_phone(value)
    except ValueError:
        raise ValueError("请输入有效的手机号或邮箱地址")


# ========== 证件验证 ==========

def validate_id_card(id_card: str) -> str:
    """
    验证身份证号格式
    
    支持15位和18位身份证号
    
    Args:
        id_card: 身份证号
    
    Returns:
        str: 验证后的身份证号
    
    Raises:
        ValueError: 如果身份证号格式不正确
    """
    if not id_card:
        raise ValueError("身份证号不能为空")
    
    id_card = id_card.strip().upper()
    
    # 15位或18位
    if len(id_card) not in [15, 18]:
        raise ValueError("身份证号必须是15位或18位")
    
    # 18位身份证号验证
    if len(id_card) == 18:
        # 前17位必须是数字
        if not id_card[:17].isdigit():
            raise ValueError("身份证号前17位必须是数字")
        
        # 最后一位可以是数字或X
        if id_card[17] not in "0123456789X":
            raise ValueError("身份证号最后一位必须是数字或X")
        
        # 简单校验码验证（可选，这里只做格式验证）
    
    # 15位身份证号验证
    elif len(id_card) == 15:
        if not id_card.isdigit():
            raise ValueError("15位身份证号必须全部是数字")
    
    return id_card


def validate_bank_card(card_number: str) -> str:
    """
    验证银行卡号格式
    
    使用Luhn算法验证银行卡号
    
    Args:
        card_number: 银行卡号
    
    Returns:
        str: 验证后的银行卡号
    
    Raises:
        ValueError: 如果银行卡号格式不正确
    """
    if not card_number:
        raise ValueError("银行卡号不能为空")
    
    card_number = card_number.strip().replace(" ", "").replace("-", "")
    
    # 必须是13-19位数字
    if not card_number.isdigit():
        raise ValueError("银行卡号必须全部是数字")
    
    if len(card_number) < 13 or len(card_number) > 19:
        raise ValueError("银行卡号长度必须在13-19位之间")
    
    # Luhn算法验证
    def luhn_check(card_num: str) -> bool:
        """Luhn算法校验"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    
    if not luhn_check(card_number):
        raise ValueError("银行卡号校验失败，请检查输入")
    
    return card_number


# ========== 日期时间验证 ==========

def validate_date_range(
    start_date: Optional[date],
    end_date: Optional[date],
    allow_none: bool = True
) -> Tuple[Optional[date], Optional[date]]:
    """
    验证日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        allow_none: 是否允许为空
    
    Returns:
        Tuple[date, date]: 验证后的日期范围
    
    Raises:
        ValueError: 如果日期范围无效
    """
    if not allow_none:
        if start_date is None:
            raise ValueError("开始日期不能为空")
        if end_date is None:
            raise ValueError("结束日期不能为空")
    
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")
        
        # 检查日期范围是否过大（可选）
        days_diff = (end_date - start_date).days
        if days_diff > 365:
            raise ValueError("日期范围不能超过365天")
    
    return start_date, end_date


def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> date:
    """
    验证日期字符串格式
    
    Args:
        date_str: 日期字符串
        format: 日期格式（默认：%Y-%m-%d）
    
    Returns:
        date: 解析后的日期对象
    
    Raises:
        ValueError: 如果日期格式不正确
    """
    if not date_str:
        raise ValueError("日期字符串不能为空")
    
    try:
        return datetime.strptime(date_str.strip(), format).date()
    except ValueError:
        raise ValueError(f"日期格式不正确，应为：{format}")


# ========== 数值验证 ==========

def validate_positive_number(value: Any, field_name: str = "数值") -> float:
    """
    验证正数
    
    Args:
        value: 数值
        field_name: 字段名称（用于错误消息）
    
    Returns:
        float: 验证后的正数
    
    Raises:
        ValueError: 如果不是正数
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name}必须是数字")
    
    if num <= 0:
        raise ValueError(f"{field_name}必须大于0")
    
    return num


def validate_non_negative_number(value: Any, field_name: str = "数值") -> float:
    """
    验证非负数
    
    Args:
        value: 数值
        field_name: 字段名称
    
    Returns:
        float: 验证后的非负数
    
    Raises:
        ValueError: 如果是负数
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name}必须是数字")
    
    if num < 0:
        raise ValueError(f"{field_name}不能为负数")
    
    return num


def validate_decimal(
    value: Any,
    min_value: Optional[Decimal] = None,
    max_value: Optional[Decimal] = None,
    precision: int = 2,
    field_name: str = "数值"
) -> Decimal:
    """
    验证Decimal数值
    
    Args:
        value: 数值
        min_value: 最小值
        max_value: 最大值
        precision: 小数精度
        field_name: 字段名称
    
    Returns:
        Decimal: 验证后的Decimal值
    
    Raises:
        ValueError: 如果数值无效
    """
    try:
        decimal_value = Decimal(str(value))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"{field_name}必须是有效的数字")
    
    # 精度检查
    if decimal_value.as_tuple().exponent < -precision:
        raise ValueError(f"{field_name}小数位数不能超过{precision}位")
    
    # 范围检查
    if min_value is not None and decimal_value < min_value:
        raise ValueError(f"{field_name}不能小于{min_value}")
    
    if max_value is not None and decimal_value > max_value:
        raise ValueError(f"{field_name}不能大于{max_value}")
    
    return decimal_value.quantize(Decimal(10) ** -precision)


# ========== 字符串验证 ==========

def validate_non_empty_string(value: str, field_name: str = "字符串", min_length: int = 1, max_length: Optional[int] = None) -> str:
    """
    验证非空字符串
    
    Args:
        value: 字符串值
        field_name: 字段名称
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        str: 验证后的字符串
    
    Raises:
        ValueError: 如果字符串无效
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name}必须是字符串")
    
    value = value.strip()
    
    if len(value) < min_length:
        raise ValueError(f"{field_name}长度不能少于{min_length}个字符")
    
    if max_length and len(value) > max_length:
        raise ValueError(f"{field_name}长度不能超过{max_length}个字符")
    
    return value


def validate_code_string(value: str, field_name: str = "编码") -> str:
    """
    验证编码字符串（字母数字下划线）
    
    Args:
        value: 编码字符串
        field_name: 字段名称
    
    Returns:
        str: 验证后的编码字符串
    
    Raises:
        ValueError: 如果编码格式不正确
    """
    if not value:
        raise ValueError(f"{field_name}不能为空")
    
    value = value.strip()
    
    # 只能包含字母、数字、下划线、连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, value):
        raise ValueError(f"{field_name}只能包含字母、数字、下划线和连字符")
    
    return value


# ========== 状态验证 ==========

def validate_status(value: str, allowed_statuses: list, field_name: str = "状态") -> str:
    """
    验证状态值
    
    Args:
        value: 状态值
        allowed_statuses: 允许的状态列表
        field_name: 字段名称
    
    Returns:
        str: 验证后的状态值
    
    Raises:
        ValueError: 如果状态值不在允许列表中
    """
    if not value:
        raise ValueError(f"{field_name}不能为空")
    
    value = value.strip().upper()
    
    allowed_upper = [s.upper() for s in allowed_statuses]
    if value not in allowed_upper:
        raise ValueError(f"{field_name}必须是以下值之一：{', '.join(allowed_statuses)}")
    
    return value


__all__ = [
    # 项目相关
    "validate_project_code",
    "validate_machine_code",
    # 联系方式
    "validate_phone",
    "validate_email",
    "validate_phone_or_email",
    # 证件
    "validate_id_card",
    "validate_bank_card",
    # 日期时间
    "validate_date_range",
    "validate_date_string",
    # 数值
    "validate_positive_number",
    "validate_non_negative_number",
    "validate_decimal",
    # 字符串
    "validate_non_empty_string",
    "validate_code_string",
    # 状态
    "validate_status",
]
