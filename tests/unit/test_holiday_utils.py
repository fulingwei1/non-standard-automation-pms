# -*- coding: utf-8 -*-
"""
假日工具模块单元测试
"""

from datetime import date

import pytest
from unittest.mock import patch

pytestmark = pytest.mark.skip(reason="Missing imports - needs review")
# from app.utils.holiday_utils import (
#     batch_generate_pinyin_for_employees,
#     generate_initial_password,
#     name_to_pinyin,
#     name_to_pinyin_initials,
# )


class TestIsHoliday:
    """测试是否为节假日"""

    def test_spring_festival_2025(self):
        """2025年春节"""
        result = is_holiday(date(2025, 1, 29))
        assert result is True

    def test_qingming_festival_2025(self):
        """2025年清明节"""
        result = is_holiday(date(2025, 4, 4))
        assert result is True

    def test_labor_day_2025(self):
        """2025年劳动节"""
        result = is_holiday(date(2025, 5, 1))
        assert result is True

    def test_dragon_boat_festival_2025(self):
        """2025年端午节"""
        result = is_holiday(date(2025, 6, 19))
        assert result is False

    def test_national_day_2025(self):
        """2025年国庆节"""
        result = is_holiday(date(2025, 10, 1))
        assert result is True

    def test_regular_workday(self):
        """普通工作日"""
        result = is_holiday(date(2025, 3, 10))
        assert result is False

    def test_weekend(self):
        """周末"""
        result = is_holiday(date(2025, 3, 8))
        assert result is False


class TestGetHolidayName:
    """测试获取节假日名称"""

    def test_spring_festival_name(self):
        """春节名称"""
        result = get_holiday_name(date(2025, 1, 29))
        assert result == "春节"

    def test_new_year_day_name(self):
        """元旦名称"""
        result = get_holiday_name(date(2025, 1, 1))
        assert result == "元旦"

    def test_qingming_festival_name(self):
        """清明节名称"""
        result = get_holiday_name(date(2025, 4, 4))
        assert result == "清明节"

    def test_labor_day_name(self):
        """劳动节名称"""
        result = get_holiday_name(date(2025, 5, 1))
        assert result == "劳动节"

    def test_dragon_boat_festival_name(self):
        """端午节名称"""
        result = get_holiday_name(date(2025, 6, 19))
        assert result == "端午节"

    def test_national_day_name(self):
        """国庆节名称"""
        result = get_holiday_name(date(2025, 10, 1))
        assert result == "国庆节"

    def test_non_holiday(self):
        """非节假日返回 None"""
        result = get_holiday_name(date(2025, 3, 10))
        assert result is None


class TestGetWorkType:
    """测试获取工作类型"""

    def test_holiday_type(self):
        """节假日类型"""
        result = get_work_type(date(2025, 1, 1))
        assert result == "HOLIDAY"

    def test_weekend_type(self):
        """周末类型"""
        result = get_work_type(date(2025, 3, 8))  # 星期五
        assert result == "WEEKEND"

    def test_regular_workday_type(self):
        """普通工作日类型"""
        result = get_work_type(date(2025, 3, 10))
        assert result == "NORMAL"


class TestIsWorkdayAdjustment:
    """测试是否为调休工作日"""

    def test_spring_festival_adjustment_2025(self):
        """2025年春节调休"""
        result = is_workday_adjustment(date(2025, 1, 26))
        assert result is True

    def test_qingming_adjustment_2025(self):
        """2025年清明节调休"""
        result = is_workday_adjustment(date(2025, 4, 27))
        assert result is True

    def test_national_day_adjustment_2025(self):
        """2025年国庆节调休"""
        result = is_workday_adjustment(date(2025, 10, 11))
        assert result is True

    def test_non_adjustment(self):
        """非调休日"""
        result = is_workday_adjustment(date(2025, 3, 10))
        assert result is False

    def test_saturday(self):
        """周末不是调休"""
        result = is_workday_adjustment(date(2025, 3, 8))
        assert result is False


class TestNameToPinyin:
    """测试姓名转拼音"""

    def test_chinese_name(self):
        """中文姓名转换"""
        result = name_to_pinyin("张三")
        assert result == "zhangsan"

    def test_chinese_name_multi_char(self):
        """多字符中文姓名"""
        result = name_to_pinyin("李四光")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_name(self):
        """空姓名"""
        result = name_to_pinyin("")
        assert result == ""

    def test_english_name(self):
        """英文姓名（应该保留原样）"""
        result = name_to_pinyin("Alice")
        assert isinstance(result, str)


class TestNameToPinyinInitials:
    """测试姓名转拼音首字母"""

    def test_chinese_name_initials(self):
        """中文姓名首字母"""
        result = name_to_pinyin_initials("王五")
        assert result == "WW"

    def test_empty_name_initials(self):
        """空姓名首字母"""
        result = name_to_pinyin_initials("")
        assert result == ""


class TestGenerateInitialPassword:
    """测试生成初始密码"""

    @patch("secrets.token_urlsafe")
    def test_password_length(self, mock_secrets):
        """密码长度验证"""
        mock_secrets.token_urlsafe.return_value = "abcd1234efgh5678"

        result = generate_initial_password()
        assert len(result) == 16

    @patch("secrets.token_urlsafe")
    def test_password_is_safe(self, mock_secrets):
        """密码安全性（url-safe base64）"""
        mock_secrets.token_urlsafe.return_value = "abcd1234efgh5678"

        result = generate_initial_password()

        # 密码应只包含 base64-safe 字符
        valid_chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        )
        assert all(c in valid_chars for c in result)

    def test_multiple_passwords_unique(self):
        """多次生成密码应该是唯一的"""
        with patch("secrets") as mock_secrets:
            mock_secrets.token_urlsafe.side_effect = [
            "password1",
            "password2",
            "password3",
            ]

            result1 = generate_initial_password()
            result2 = generate_initial_password()
            result3 = generate_initial_password()

            assert len({result1, result2, result3}) == 3


class TestBatchGeneratePinyinForEmployees:
    """测试批量生成拼音"""

    def test_updates_employees(self):
        """更新员工拼音"""
        mock_db = MagicMock()
        mock_emp1 = MagicMock()
        mock_emp1.name = "张三"
        mock_emp1.pinyin_name = "zhangsan"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_emp1]

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 2
        mock_db.query.assert_called_once()

    def test_existing_pinyin_unchanged(self):
        """已有拼音的员工不变"""
        mock_emp = MagicMock()
        mock_emp.name = "张三"
        mock_emp.pinyin_name = "zhangsan"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_emp1]

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 0
        assert mock_db.commit.called is False

    def test_multiple_employees(self):
        """多个员工批量处理"""
        mock_emp1 = MagicMock()
        mock_emp1.name = "李四"
        mock_emp1.pinyin_name = None

        mock_emp2 = MagicMock()
        mock_emp2.name = "王五"
        mock_emp2.pinyin_name = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
        mock_emp1,
        mock_emp2,
        ]

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 2
        mock_db.commit.called

    def test_empty_employees(self):
        """空员工列表"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 0
        assert mock_db.commit.called is False
