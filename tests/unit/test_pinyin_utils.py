# -*- coding: utf-8 -*-
"""
拼音工具模块测试
"""

from unittest.mock import MagicMock, patch


from app.utils.pinyin_utils import (
    batch_generate_pinyin_for_employees,
    generate_initial_password,
    name_to_pinyin,
    name_to_pinyin_initials,
)


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

    @patch("app.utils.pinyin_utils.secrets")
    def test_password_length(self, mock_secrets):
        """密码长度验证"""
        mock_secrets.token_urlsafe.return_value = "abcd1234efgh5678"

        result = generate_initial_password()
        assert len(result) == 16

    @patch("app.utils.pinyin_utils.secrets")
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
        with patch("app.utils.pinyin_utils.secrets") as mock_secrets:
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
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 0
        mock_db.query.assert_called_once()

    def test_existing_pinyin_unchanged(self):
        """已有拼音的员工不变"""
        mock_emp = MagicMock()
        mock_emp.name = "张三"
        mock_emp.pinyin_name = "zhangsan"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_emp]

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
        assert mock_db.commit.called

    def test_empty_employees(self):
        """空员工列表"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = batch_generate_pinyin_for_employees(mock_db)

        assert result == 0
        assert mock_db.commit.called is False
