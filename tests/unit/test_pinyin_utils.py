# -*- coding: utf-8 -*-
"""
拼音工具模块单元测试
"""

from unittest.mock import MagicMock


from app.utils.pinyin_utils import (
    batch_generate_pinyin_for_employees,
    generate_initial_password,
    generate_unique_username,
    name_to_pinyin,
    name_to_pinyin_initials,
)


class TestNameToPinyin:
    """测试 name_to_pinyin 函数"""

    def test_chinese_name(self):
        """测试中文姓名转拼音"""
        result = name_to_pinyin("姚洪")
        assert result == "yaohong"

    def test_simple_chinese(self):
        """测试简单中文"""
        result = name_to_pinyin("张三")
        assert result == "zhangsan"

    def test_complex_chinese(self):
        """测试复杂中文姓名"""
        result = name_to_pinyin("欧阳修")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_string(self):
        """测试空字符串"""
        result = name_to_pinyin("")
        assert result == ""

    def test_none_value(self):
        """测试 None 值"""
        result = name_to_pinyin(None)
        assert result == ""

    def test_single_character(self):
        """测试单个中文字符"""
        result = name_to_pinyin("王")
        assert isinstance(result, str)
        assert len(result) > 0


class TestNameToPinyinInitials:
    """测试 name_to_pinyin_initials 函数"""

    def test_chinese_name_initials(self):
        """测试中文姓名转拼音首字母"""
        result = name_to_pinyin_initials("姚洪")
        assert result == "YH"

    def test_simple_name_initials(self):
        """测试简单姓名首字母"""
        result = name_to_pinyin_initials("张三")
        assert result == "ZS"

    def test_three_character_name(self):
        """测试三字姓名首字母"""
        result = name_to_pinyin_initials("王小明")
        assert result == "WXM"

    def test_complex_name_initials(self):
        """测试复杂复姓首字母"""
        result = name_to_pinyin_initials("欧阳修")
        assert isinstance(result, str)
        assert len(result) == 3

    def test_empty_string_initials(self):
        """测试空字符串首字母"""
        result = name_to_pinyin_initials("")
        assert result == ""

    def test_none_value_initials(self):
        """测试 None 值首字母"""
        result = name_to_pinyin_initials(None)
        assert result == ""

    def test_single_character_initials(self):
        """测试单个字符首字母"""
        result = name_to_pinyin_initials("王")
        assert isinstance(result, str)
        assert len(result) == 1


class TestGenerateInitialPassword:
    """测试 generate_initial_password 函数"""

    def test_password_length(self):
        """测试密码长度为 16 字符"""
        password = generate_initial_password()
        assert len(password) == 16

    def test_password_is_string(self):
        """测试密码是字符串"""
        password = generate_initial_password()
        assert isinstance(password, str)

    def test_password_always_different(self):
        """测试每次生成不同的密码"""
        passwords = [generate_initial_password() for _ in range(10)]
        unique_passwords = set(passwords)
        assert len(unique_passwords) > 1

    def test_password_with_deprecated_params(self):
        """测试带已废弃参数仍能正常工作"""
        password = generate_initial_password(
            username="testuser", id_card="123456", employee_code="EMP001"
        )
        assert len(password) == 16

    def test_password_without_params(self):
        """测试不带参数生成密码"""
        password = generate_initial_password()
        assert len(password) == 16


class TestBatchGeneratePinyinForEmployees:
    """测试 batch_generate_pinyin_for_employees 函数"""

    def test_batch_with_empty_database(self):
        """测试空数据库"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = batch_generate_pinyin_for_employees(mock_db)
        assert result == 0

    def test_batch_with_employees(self):
        """测试批量更新员工拼音"""
        mock_db = MagicMock()
        mock_employee1 = MagicMock()
        mock_employee1.name = "张三"
        mock_employee1.pinyin_name = None

        mock_employee2 = MagicMock()
        mock_employee2.name = "李四"
        mock_employee2.pinyin_name = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_employee1,
            mock_employee2,
        ]

        result = batch_generate_pinyin_for_employees(mock_db)
        assert result == 2

    def test_batch_commit_called(self):
        """测试有更新时调用 commit"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.name = "王五"
        mock_employee.pinyin_name = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_employee
        ]

        batch_generate_pinyin_for_employees(mock_db)
        mock_db.commit.assert_called_once()

    def test_batch_no_employees_with_null_pinyin(self):
        """测试没有需要更新的员工"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = batch_generate_pinyin_for_employees(mock_db)
        assert result == 0
        mock_db.commit.assert_not_called()

    def test_batch_employee_without_name(self):
        """测试没有姓名的员工"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.name = None
        mock_employee.pinyin_name = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_employee
        ]

        result = batch_generate_pinyin_for_employees(mock_db)
        assert result == 0


class TestGenerateUniqueUsername:
    """测试 generate_unique_username 函数"""

    def test_generate_unique_username_first_available(self):
        """测试生成唯一用户名，第一次就可用"""
        from unittest.mock import Mock
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 用户名不存在
        
        result = generate_unique_username("张三", mock_db)
        assert result == "zhangsan"

    def test_generate_unique_username_with_existing(self):
        """测试生成唯一用户名，需要添加数字后缀"""
        from unittest.mock import Mock
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 第一次查询返回已存在的用户，第二次返回 None
        mock_query.first.side_effect = [Mock(), None]
        
        result = generate_unique_username("张三", mock_db)
        assert result == "zhangsan2"

    def test_generate_unique_username_with_existing_set(self):
        """测试使用 existing_usernames 集合避免重复查询"""
        from unittest.mock import Mock
        
        mock_db = Mock()
        existing = {"zhangsan", "zhangsan2"}
        
        # 使用 existing_usernames，应该直接返回 zhangsan3
        result = generate_unique_username("张三", mock_db, existing_usernames=existing)
        assert result == "zhangsan3"
        # 不应该查询数据库
        mock_db.query.assert_not_called()

    def test_generate_unique_username_empty_name(self):
        """测试空名称时使用默认用户名"""
        from unittest.mock import Mock
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = generate_unique_username("", mock_db)
        assert result == "user"

    def test_generate_unique_username_multiple_conflicts(self):
        """测试多个冲突时递增数字"""
        from unittest.mock import Mock
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 前两次返回已存在，第三次返回 None
        mock_query.first.side_effect = [Mock(), Mock(), None]
        
        result = generate_unique_username("张三", mock_db)
        assert result == "zhangsan3"
