# -*- coding: utf-8 -*-
"""
Comprehensive tests for app/core/schemas/validators.py
Standalone – no DB or fixtures required.
"""
import pytest
from decimal import Decimal
from datetime import date

from app.core.schemas.validators import (
    validate_project_code,
    validate_machine_code,
    validate_phone,
    validate_email,
    validate_phone_or_email,
    validate_id_card,
    validate_bank_card,
    validate_date_range,
    validate_date_string,
    validate_positive_number,
    validate_non_negative_number,
    validate_decimal,
    validate_non_empty_string,
    validate_code_string,
    validate_status,
)


# ========== validate_project_code ==========

class TestValidateProjectCode:
    def test_valid_code(self):
        assert validate_project_code("PJ250101001") == "PJ250101001"

    def test_lowercase_accepted(self):
        # Should be normalised to upper
        assert validate_project_code("pj250101001") == "PJ250101001"

    def test_strips_whitespace(self):
        assert validate_project_code("  PJ250101001  ") == "PJ250101001"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_project_code("")

    def test_none_raises(self):
        with pytest.raises((ValueError, AttributeError)):
            validate_project_code(None)

    def test_wrong_prefix_raises(self):
        with pytest.raises(ValueError, match="PJ开头"):
            validate_project_code("AB250101001")

    def test_wrong_length_short(self):
        with pytest.raises(ValueError, match="11位"):
            validate_project_code("PJ25010100")

    def test_wrong_length_long(self):
        with pytest.raises(ValueError, match="11位"):
            validate_project_code("PJ2501010012")

    def test_invalid_date_raises(self):
        # Month 99 is invalid
        with pytest.raises(ValueError, match="日期部分无效"):
            validate_project_code("PJ259901001")

    def test_invalid_day_raises(self):
        with pytest.raises(ValueError, match="日期部分无效"):
            validate_project_code("PJ250132001")  # Jan 32 is invalid

    def test_non_digit_seq_raises(self):
        with pytest.raises(ValueError, match="序号部分"):
            validate_project_code("PJ250101ABC")


# ========== validate_machine_code ==========

class TestValidateMachineCode:
    def test_valid_code(self):
        assert validate_machine_code("PN001") == "PN001"

    def test_lowercase_normalised(self):
        assert validate_machine_code("pn001") == "PN001"

    def test_strips_whitespace(self):
        assert validate_machine_code("  PN001  ") == "PN001"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_machine_code("")

    def test_wrong_prefix_raises(self):
        with pytest.raises(ValueError, match="PN开头"):
            validate_machine_code("AB001")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="至少为3位"):
            validate_machine_code("PN")


# ========== validate_phone ==========

class TestValidatePhone:
    def test_valid_phone(self):
        assert validate_phone("13812345678") == "13812345678"

    def test_strips_spaces_and_dashes(self):
        assert validate_phone("138-1234-5678") == "13812345678"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_phone("")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="手机号格式不正确"):
            validate_phone("1381234567")

    def test_starting_with_1_and_wrong_second_digit(self):
        with pytest.raises(ValueError, match="手机号格式不正确"):
            validate_phone("12345678901")

    def test_starting_with_non_1(self):
        with pytest.raises(ValueError, match="手机号格式不正确"):
            validate_phone("23812345678")


# ========== validate_email ==========

class TestValidateEmail:
    def test_valid_email(self):
        result = validate_email("Test@Example.COM")
        assert result == "test@example.com"

    def test_strips_whitespace(self):
        result = validate_email("  user@example.com  ")
        assert result == "user@example.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_email("")

    def test_no_at_sign_raises(self):
        with pytest.raises(ValueError, match="邮箱格式不正确"):
            validate_email("userexample.com")

    def test_no_domain_raises(self):
        with pytest.raises(ValueError, match="邮箱格式不正确"):
            validate_email("user@")

    def test_too_long_raises(self):
        long_email = "a" * 250 + "@b.com"
        with pytest.raises(ValueError, match="过长"):
            validate_email(long_email)


# ========== validate_phone_or_email ==========

class TestValidatePhoneOrEmail:
    def test_valid_phone(self):
        result = validate_phone_or_email("13812345678")
        assert result == "13812345678"

    def test_valid_email(self):
        result = validate_phone_or_email("user@example.com")
        assert result == "user@example.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_phone_or_email("")

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError, match="手机号或邮箱"):
            validate_phone_or_email("not_a_phone_or_email")

    def test_invalid_email_format_raises(self):
        with pytest.raises(ValueError):
            validate_phone_or_email("bad@")


# ========== validate_id_card ==========

class TestValidateIdCard:
    def test_valid_18_digit(self):
        # Valid 18-digit ID
        result = validate_id_card("110101199001011234")
        assert result == "110101199001011234"

    def test_valid_18_digit_with_x(self):
        result = validate_id_card("11010119900101123X")
        assert result == "11010119900101123X"

    def test_lowercase_x_normalised(self):
        result = validate_id_card("11010119900101123x")
        assert result == "11010119900101123X"

    def test_valid_15_digit(self):
        result = validate_id_card("110101900101123")
        assert result == "110101900101123"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_id_card("")

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError, match="15位或18位"):
            validate_id_card("12345")

    def test_18_digit_non_digit_prefix_raises(self):
        with pytest.raises(ValueError, match="17位必须是数字"):
            validate_id_card("1101011990010112XA")

    def test_18_digit_invalid_last_char_raises(self):
        with pytest.raises(ValueError, match="最后一位"):
            validate_id_card("11010119900101123A")

    def test_15_digit_with_letters_raises(self):
        with pytest.raises(ValueError, match="全部是数字"):
            validate_id_card("11010190010112A")


# ========== validate_bank_card ==========

class TestValidateBankCard:
    def test_valid_card(self):
        # Known Luhn-valid test card number
        result = validate_bank_card("4532015112830366")
        assert result == "4532015112830366"

    def test_strips_spaces_and_dashes(self):
        result = validate_bank_card("4532-0151-1283-0366")
        assert result == "4532015112830366"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_bank_card("")

    def test_non_digit_raises(self):
        with pytest.raises(ValueError, match="全部是数字"):
            validate_bank_card("4532ABCD12830366")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="13-19位"):
            validate_bank_card("123456789012")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="13-19位"):
            validate_bank_card("12345678901234567890")

    def test_luhn_check_fails(self):
        # A number that passes length but fails Luhn
        with pytest.raises(ValueError, match="校验失败"):
            validate_bank_card("1234567890123456")


# ========== validate_date_range ==========

class TestValidateDateRange:
    def test_valid_range(self):
        s = date(2025, 1, 1)
        e = date(2025, 6, 30)
        result = validate_date_range(s, e)
        assert result == (s, e)

    def test_both_none_allowed(self):
        result = validate_date_range(None, None, allow_none=True)
        assert result == (None, None)

    def test_none_start_not_allowed_raises(self):
        with pytest.raises(ValueError, match="开始日期不能为空"):
            validate_date_range(None, date(2025, 6, 30), allow_none=False)

    def test_none_end_not_allowed_raises(self):
        with pytest.raises(ValueError, match="结束日期不能为空"):
            validate_date_range(date(2025, 1, 1), None, allow_none=False)

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
            validate_date_range(date(2025, 6, 30), date(2025, 1, 1))

    def test_range_over_365_days_raises(self):
        s = date(2024, 1, 1)
        e = date(2025, 6, 30)  # > 365 days
        with pytest.raises(ValueError, match="不能超过365天"):
            validate_date_range(s, e)


# ========== validate_date_string ==========

class TestValidateDateString:
    def test_valid_date(self):
        result = validate_date_string("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_strips_whitespace(self):
        result = validate_date_string("  2025-01-15  ")
        assert result == date(2025, 1, 15)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_date_string("")

    def test_wrong_format_raises(self):
        with pytest.raises(ValueError, match="格式不正确"):
            validate_date_string("15/01/2025")

    def test_custom_format(self):
        result = validate_date_string("15/01/2025", format="%d/%m/%Y")
        assert result == date(2025, 1, 15)


# ========== validate_positive_number ==========

class TestValidatePositiveNumber:
    def test_valid_int(self):
        assert validate_positive_number(5) == 5.0

    def test_valid_float(self):
        assert validate_positive_number(3.14) == 3.14

    def test_valid_string_number(self):
        assert validate_positive_number("2.5") == 2.5

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="必须大于0"):
            validate_positive_number(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="必须大于0"):
            validate_positive_number(-1)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="必须是数字"):
            validate_positive_number("abc")

    def test_custom_field_name_in_error(self):
        with pytest.raises(ValueError, match="金额"):
            validate_positive_number(-10, field_name="金额")


# ========== validate_non_negative_number ==========

class TestValidateNonNegativeNumber:
    def test_zero_allowed(self):
        assert validate_non_negative_number(0) == 0.0

    def test_positive_allowed(self):
        assert validate_non_negative_number(5.5) == 5.5

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="不能为负数"):
            validate_non_negative_number(-0.1)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="必须是数字"):
            validate_non_negative_number("abc")

    def test_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            validate_non_negative_number(None)


# ========== validate_decimal ==========

class TestValidateDecimal:
    def test_valid_value(self):
        result = validate_decimal("12.50")
        assert result == Decimal("12.50")

    def test_min_value_ok(self):
        result = validate_decimal("5.00", min_value=Decimal("0"))
        assert result == Decimal("5.00")

    def test_min_value_fails(self):
        with pytest.raises(ValueError, match="不能小于"):
            validate_decimal("-1.00", min_value=Decimal("0"))

    def test_max_value_ok(self):
        result = validate_decimal("9.99", max_value=Decimal("10"))
        assert result == Decimal("9.99")

    def test_max_value_fails(self):
        with pytest.raises(ValueError, match="不能大于"):
            validate_decimal("15.00", max_value=Decimal("10"))

    def test_precision_exceeded_raises(self):
        with pytest.raises(ValueError, match="小数位数"):
            validate_decimal("12.125", precision=2)

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError, match="有效的数字"):
            validate_decimal("not_a_number")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_decimal(None)


# ========== validate_non_empty_string ==========

class TestValidateNonEmptyString:
    def test_valid_string(self):
        assert validate_non_empty_string("hello") == "hello"

    def test_strips_whitespace(self):
        assert validate_non_empty_string("  hello  ") == "hello"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="长度不能少于"):
            validate_non_empty_string("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="长度不能少于"):
            validate_non_empty_string("   ")

    def test_min_length_constraint(self):
        with pytest.raises(ValueError, match="长度不能少于"):
            validate_non_empty_string("ab", min_length=5)

    def test_max_length_constraint(self):
        with pytest.raises(ValueError, match="长度不能超过"):
            validate_non_empty_string("hello world", max_length=5)

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="必须是字符串"):
            validate_non_empty_string(123)


# ========== validate_code_string ==========

class TestValidateCodeString:
    def test_valid_code(self):
        assert validate_code_string("ABC_123") == "ABC_123"

    def test_with_hyphens(self):
        assert validate_code_string("code-123") == "code-123"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_code_string("")

    def test_special_chars_raises(self):
        with pytest.raises(ValueError, match="只能包含"):
            validate_code_string("code@123")

    def test_spaces_raise(self):
        with pytest.raises(ValueError, match="只能包含"):
            validate_code_string("code 123")


# ========== validate_status ==========

class TestValidateStatus:
    def test_valid_status(self):
        result = validate_status("ACTIVE", ["ACTIVE", "INACTIVE", "PENDING"])
        assert result == "ACTIVE"

    def test_case_insensitive(self):
        result = validate_status("active", ["ACTIVE", "INACTIVE"])
        assert result == "ACTIVE"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_status("", ["ACTIVE"])

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="必须是以下值之一"):
            validate_status("UNKNOWN", ["ACTIVE", "INACTIVE"])

    def test_strips_whitespace(self):
        result = validate_status("  ACTIVE  ", ["ACTIVE"])
        assert result == "ACTIVE"
