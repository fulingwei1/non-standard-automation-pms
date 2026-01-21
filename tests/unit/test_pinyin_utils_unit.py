"""
Unit tests for pinyin_utils utility functions.

Tests coverage for:
- name_to_pinyin function
- name_to_pinyin_initials function
- generate_unique_username function
- generate_initial_password function
"""

from app.utils.pinyin_utils import (
    name_to_pinyin,
    name_to_pinyin_initials,
    generate_initial_password,
)


class TestNameToPinyin:
    """Test name_to_pinyin function."""

    def test_chinese_to_pinyin(self):
        """Test converting Chinese name to pinyin."""
        result = name_to_pinyin("张三")

        assert result == "zhangsan"

    def test_chinese_two_characters(self):
        """Test Chinese name with two characters."""
        result = name_to_pinyin("王芳")

        assert result == "wangfang"

    def test_chinese_three_characters(self):
        """Test Chinese name with three characters."""
        result = name_to_pinyin("李明华")

        assert result == "liminghua"

    def test_empty_string(self):
        """Test empty string returns empty."""
        result = name_to_pinyin("")

        assert result == ""

    def test_lowercase_output(self):
        """Test output is lowercase."""
        result = name_to_pinyin("张伟")

        assert result == "zhangwei"

    def test_no_spaces(self):
        """Test output has no spaces."""
        result = name_to_pinyin("赵六")

        assert " " not in result


class TestNameToPinyinInitials:
    """Test name_to_pinyin_initials function."""

    def test_chinese_to_initials(self):
        """Test converting Chinese name to initials."""
        result = name_to_pinyin_initials("张三")

        assert result == "ZS"

    def test_two_characters(self):
        """Test two character name."""
        result = name_to_pinyin_initials("王芳")

        assert result == "WF"

    def test_three_characters(self):
        """Test three character name."""
        result = name_to_pinyin_initials("李明华")

        assert result == "LMH"

    def test_empty_string(self):
        """Test empty string returns empty."""
        result = name_to_pinyin_initials("")

        assert result == ""

    def test_uppercase_output(self):
        """Test output is uppercase."""
        result = name_to_pinyin_initials("赵六")

        assert result.isupper()

    def test_no_spaces(self):
        """Test output has no spaces."""
        result = name_to_pinyin_initials("刘德华")

        assert " " not in result


class TestGenerateInitialPassword:
    """Test generate_initial_password function."""

    def test_password_format(self):
        """Test password has correct format."""
        password = generate_initial_password()

        assert len(password) == 16
        assert isinstance(password, str)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_special_characters_in_name(self):
        """Test handling of special characters in name."""
        result = name_to_pinyin("张三-Zhang")

        assert "zhang" in result.lower()

    def test_numbers_in_name(self):
        """Test handling of numbers in name."""
        result = name_to_pinyin("张三123")

        assert "zhang" in result.lower()

    def test_mixed_case_input(self):
        """Test mixed case input."""
        result1 = name_to_pinyin("张三")
        result2 = name_to_pinyin("ZHANGSAN")

        assert result1 == result2

    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        result = name_to_pinyin("  张三  ")

        assert result == "zhangsan"
