# -*- coding: utf-8 -*-
"""
统一验证器测试
"""

import pytest
from decimal import Decimal
from datetime import date
from app.core.schemas.validators import (
    validate_project_code,
    validate_machine_code,
    validate_phone,
    validate_email,
    validate_id_card,
    validate_bank_card,
    validate_date_range,
    validate_positive_number,
    validate_decimal,
    validate_non_empty_string,
    validate_status,
)


class TestProjectCodeValidator:
    """项目编码验证器测试"""
    
    def test_valid_project_code(self):
        """测试有效项目编码"""
        assert validate_project_code("PJ250101001") == "PJ250101001"
    
    def test_invalid_prefix(self):
        """测试无效前缀"""
        with pytest.raises(ValueError, match="必须以PJ开头"):
            validate_project_code("INVALID001")
    
    def test_invalid_length(self):
        """测试无效长度"""
        with pytest.raises(ValueError, match="长度必须为11位"):
            validate_project_code("PJ25010100")
    
    def test_invalid_date(self):
        """测试无效日期"""
        with pytest.raises(ValueError, match="日期部分无效"):
            validate_project_code("PJ250132001")  # 无效月份


class TestPhoneValidator:
    """手机号验证器测试"""
    
    def test_valid_phone(self):
        """测试有效手机号"""
        assert validate_phone("13800138000") == "13800138000"
        assert validate_phone("15912345678") == "15912345678"
    
    def test_invalid_phone(self):
        """测试无效手机号"""
        with pytest.raises(ValueError, match="手机号格式不正确"):
            validate_phone("12345678901")  # 不是1开头
            validate_phone("1380013800")   # 长度不对
            validate_phone("12800138000")   # 第二位不对


class TestEmailValidator:
    """邮箱验证器测试"""
    
    def test_valid_email(self):
        """测试有效邮箱"""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"
    
    def test_invalid_email(self):
        """测试无效邮箱"""
        with pytest.raises(ValueError, match="邮箱格式不正确"):
            validate_email("invalid")
            validate_email("test@")
            validate_email("@example.com")


class TestNumberValidators:
    """数值验证器测试"""
    
    def test_validate_positive_number(self):
        """测试正数验证"""
        assert validate_positive_number(10) == 10.0
        assert validate_positive_number("10") == 10.0
        
        with pytest.raises(ValueError, match="必须大于0"):
            validate_positive_number(0)
            validate_positive_number(-1)
    
    def test_validate_decimal(self):
        """测试Decimal验证"""
        assert validate_decimal(10.5, precision=2) == Decimal("10.50")
        
        with pytest.raises(ValueError, match="小数位数不能超过"):
            validate_decimal(10.123, precision=2)
        
        with pytest.raises(ValueError, match="不能小于"):
            validate_decimal(-1, min_value=Decimal("0"))


class TestStringValidators:
    """字符串验证器测试"""
    
    def test_validate_non_empty_string(self):
        """测试非空字符串验证"""
        assert validate_non_empty_string("test") == "test"
        assert validate_non_empty_string("  test  ") == "test"  # 自动trim
        
        with pytest.raises(ValueError, match="长度不能少于"):
            validate_non_empty_string("", min_length=2)
        
        with pytest.raises(ValueError, match="长度不能超过"):
            validate_non_empty_string("a" * 101, max_length=100)


class TestStatusValidator:
    """状态验证器测试"""
    
    def test_validate_status(self):
        """测试状态验证"""
        assert validate_status("ACTIVE", ["ACTIVE", "INACTIVE"]) == "ACTIVE"
        assert validate_status("active", ["ACTIVE", "INACTIVE"]) == "ACTIVE"  # 自动转大写
        
        with pytest.raises(ValueError, match="必须是以下值之一"):
            validate_status("INVALID", ["ACTIVE", "INACTIVE"])


class TestDateValidators:
    """日期验证器测试"""
    
    def test_validate_date_range(self):
        """测试日期范围验证"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        
        result = validate_date_range(start, end)
        assert result == (start, end)
        
        with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
            validate_date_range(end, start)
        
        with pytest.raises(ValueError, match="日期范围不能超过365天"):
            validate_date_range(start, date(2026, 1, 2))
