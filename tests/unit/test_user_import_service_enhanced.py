# -*- coding: utf-8 -*-
"""
用户导入服务增强单元测试
覆盖所有核心方法和边界条件
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO
from datetime import datetime

import pandas as pd
import pytest

from app.services.user_import_service import UserImportService
from app.models.user import User, Role, UserRole


class TestUserImportServiceValidation(unittest.TestCase):
    """文件格式验证测试"""

    def test_validate_file_format_xlsx(self):
        """测试 .xlsx 文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.xlsx"))
        self.assertTrue(UserImportService.validate_file_format("data.XLSX"))

    def test_validate_file_format_xls(self):
        """测试 .xls 文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.xls"))
        self.assertTrue(UserImportService.validate_file_format("data.XLS"))

    def test_validate_file_format_csv(self):
        """测试 .csv 文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.csv"))
        self.assertTrue(UserImportService.validate_file_format("data.CSV"))

    def test_validate_file_format_invalid(self):
        """测试无效文件格式"""
        self.assertFalse(UserImportService.validate_file_format("users.txt"))
        self.assertFalse(UserImportService.validate_file_format("users.pdf"))
        self.assertFalse(UserImportService.validate_file_format("users.doc"))


class TestUserImportServiceReadFile(unittest.TestCase):
    """文件读取测试"""

    @patch('pandas.read_excel')
    def test_read_excel_file_from_path(self, mock_read_excel):
        """测试从路径读取 Excel 文件"""
        mock_df = pd.DataFrame({"用户名": ["test"]})
        mock_read_excel.return_value = mock_df

        result = UserImportService.read_file("test.xlsx")

        mock_read_excel.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_csv')
    def test_read_csv_file_from_path(self, mock_read_csv):
        """测试从路径读取 CSV 文件"""
        mock_df = pd.DataFrame({"用户名": ["test"]})
        mock_read_csv.return_value = mock_df

        result = UserImportService.read_file("test.csv")

        mock_read_csv.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_excel')
    def test_read_excel_from_bytes(self, mock_read_excel):
        """测试从字节流读取 Excel"""
        mock_df = pd.DataFrame({"用户名": ["test"]})
        mock_read_excel.return_value = mock_df

        file_content = b"fake excel content"
        result = UserImportService.read_file("test.xlsx", file_content=file_content)

        mock_read_excel.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_csv')
    def test_read_csv_from_bytes(self, mock_read_csv):
        """测试从字节流读取 CSV"""
        mock_df = pd.DataFrame({"用户名": ["test"]})
        mock_read_csv.return_value = mock_df

        file_content = b"fake csv content"
        result = UserImportService.read_file("test.csv", file_content=file_content)

        mock_read_csv.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_excel')
    def test_read_file_with_whitespace_columns(self, mock_read_excel):
        """测试读取带空格的列名"""
        mock_df = pd.DataFrame({" 用户名 ": ["test"], "邮箱  ": ["test@example.com"]})
        mock_read_excel.return_value = mock_df

        result = UserImportService.read_file("test.xlsx")

        # 验证列名已去除空格
        self.assertIn("用户名", result.columns)
        self.assertIn("邮箱", result.columns)

    @patch('pandas.read_excel')
    def test_read_file_exception(self, mock_read_excel):
        """测试文件读取异常"""
        mock_read_excel.side_effect = Exception("File not found")

        with self.assertRaises(ValueError) as context:
            UserImportService.read_file("invalid.xlsx")

        self.assertIn("文件读取失败", str(context.exception))


class TestUserImportServiceNormalizeColumns(unittest.TestCase):
    """列名标准化测试"""

    def test_normalize_chinese_columns(self):
        """测试标准化中文列名"""
        df = pd.DataFrame({
            "用户名": ["test"],
            "真实姓名": ["测试"],
            "邮箱": ["test@example.com"]
        })

        result = UserImportService.normalize_columns(df)

        self.assertIn("username", result.columns)
        self.assertIn("real_name", result.columns)
        self.assertIn("email", result.columns)

    def test_normalize_english_columns(self):
        """测试标准化英文列名"""
        df = pd.DataFrame({
            "Username": ["test"],
            "Real Name": ["Test User"],
            "Email": ["test@example.com"]
        })

        result = UserImportService.normalize_columns(df)

        self.assertIn("username", result.columns)
        self.assertIn("real_name", result.columns)
        self.assertIn("email", result.columns)

    def test_normalize_mixed_columns(self):
        """测试标准化混合列名"""
        df = pd.DataFrame({
            "用户名": ["test"],
            "Email": ["test@example.com"],
            "手机号": ["13800138000"]
        })

        result = UserImportService.normalize_columns(df)

        self.assertIn("username", result.columns)
        self.assertIn("email", result.columns)
        self.assertIn("phone", result.columns)

    def test_normalize_unmapped_columns(self):
        """测试未映射的列名保持不变"""
        df = pd.DataFrame({
            "用户名": ["test"],
            "Custom Field": ["value"]
        })

        result = UserImportService.normalize_columns(df)

        self.assertIn("username", result.columns)
        self.assertIn("Custom Field", result.columns)


class TestUserImportServiceValidateDataFrame(unittest.TestCase):
    """DataFrame 结构验证测试"""

    def test_validate_dataframe_success(self):
        """测试有效的 DataFrame"""
        df = pd.DataFrame({
            "username": ["test"],
            "real_name": ["测试"],
            "email": ["test@example.com"]
        })

        errors = UserImportService.validate_dataframe(df)

        self.assertEqual(len(errors), 0)

    def test_validate_dataframe_missing_required_fields(self):
        """测试缺少必填字段"""
        df = pd.DataFrame({
            "username": ["test"],
            "email": ["test@example.com"]
        })

        errors = UserImportService.validate_dataframe(df)

        self.assertEqual(len(errors), 1)
        self.assertIn("缺少必填列", errors[0])
        self.assertIn("real_name", errors[0])

    def test_validate_dataframe_empty(self):
        """测试空 DataFrame"""
        df = pd.DataFrame({
            "username": [],
            "real_name": [],
            "email": []
        })

        errors = UserImportService.validate_dataframe(df)

        self.assertEqual(len(errors), 1)
        self.assertIn("没有数据", errors[0])

    def test_validate_dataframe_exceed_limit(self):
        """测试超过最大导入限制"""
        # 创建超过限制的数据
        data = {
            "username": [f"user{i}" for i in range(501)],
            "real_name": [f"User {i}" for i in range(501)],
            "email": [f"user{i}@example.com" for i in range(501)]
        }
        df = pd.DataFrame(data)

        errors = UserImportService.validate_dataframe(df)

        self.assertEqual(len(errors), 1)
        self.assertIn("不能超过", errors[0])
        self.assertIn("500", errors[0])

    def test_validate_dataframe_multiple_errors(self):
        """测试多个验证错误"""
        df = pd.DataFrame({
            "username": []
        })

        errors = UserImportService.validate_dataframe(df)

        self.assertGreaterEqual(len(errors), 2)


class TestUserImportServiceValidateRow(unittest.TestCase):
    """单行数据验证测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.existing_usernames = set()
        self.existing_emails = set()

    def test_validate_row_success(self):
        """测试有效的行数据"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000"
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNone(error)

    def test_validate_row_missing_required_field(self):
        """测试缺少必填字段"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "",
            "email": "test@example.com"
        })

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("不能为空", error)

    def test_validate_row_username_too_short(self):
        """测试用户名过短"""
        row = pd.Series({
            "username": "ab",
            "real_name": "测试",
            "email": "test@example.com"
        })

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("长度必须在3-50个字符之间", error)

    def test_validate_row_username_too_long(self):
        """测试用户名过长"""
        row = pd.Series({
            "username": "a" * 51,
            "real_name": "测试",
            "email": "test@example.com"
        })

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("长度必须在3-50个字符之间", error)

    def test_validate_row_duplicate_username_in_file(self):
        """测试文件内用户名重复"""
        self.existing_usernames.add("testuser")

        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com"
        })

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("重复", error)

    def test_validate_row_username_exists_in_db(self):
        """测试用户名在数据库中已存在"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com"
        })

        mock_user = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("已存在于系统中", error)

    def test_validate_row_invalid_email_format(self):
        """测试无效的邮箱格式"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "invalid-email"
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("邮箱格式不正确", error)

    def test_validate_row_duplicate_email(self):
        """测试邮箱重复"""
        self.existing_emails.add("test@example.com")

        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com"
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("邮箱", error)
        self.assertIn("重复", error)

    def test_validate_row_invalid_phone(self):
        """测试无效的手机号"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com",
            "phone": "123"
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNotNone(error)
        self.assertIn("手机号格式不正确", error)

    def test_validate_row_valid_phone_with_dashes(self):
        """测试带连字符的有效手机号"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com",
            "phone": "138-0013-8000"
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        error = UserImportService.validate_row(
            row, 2, self.mock_db, self.existing_usernames, self.existing_emails
        )

        self.assertIsNone(error)


class TestUserImportServiceGetOrCreateRole(unittest.TestCase):
    """角色获取/创建测试"""

    def setUp(self):
        self.mock_db = MagicMock()

    def test_get_existing_role(self):
        """测试获取已存在的角色"""
        mock_role = MagicMock(spec=Role)
        mock_role.role_name = "管理员"

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        result = UserImportService.get_or_create_role(self.mock_db, "管理员", tenant_id=1)

        self.assertEqual(result, mock_role)

    def test_get_role_not_found(self):
        """测试角色不存在时返回 None"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = UserImportService.get_or_create_role(self.mock_db, "不存在的角色", tenant_id=1)

        self.assertIsNone(result)

    def test_get_role_without_tenant(self):
        """测试不指定租户获取角色"""
        mock_role = MagicMock(spec=Role)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        result = UserImportService.get_or_create_role(self.mock_db, "管理员", tenant_id=None)

        self.assertEqual(result, mock_role)


class TestUserImportServiceCreateUserFromRow(unittest.TestCase):
    """从行创建用户测试"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_with_all_fields(self, mock_hash):
        """测试创建包含所有字段的用户"""
        mock_hash.return_value = "hashed_password"

        row = pd.Series({
            "username": "testuser",
            "password": "mypassword",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000",
            "employee_no": "EMP001",
            "department": "技术部",
            "position": "工程师",
            "is_active": "是"
        })

        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1, tenant_id=1
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.real_name, "测试用户")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.phone, "13800138000")
        self.assertEqual(user.employee_no, "EMP001")
        self.assertEqual(user.department, "技术部")
        self.assertEqual(user.position, "工程师")
        self.assertTrue(user.is_active)
        mock_hash.assert_called_with("mypassword")

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_with_default_password(self, mock_hash):
        """测试使用默认密码创建用户"""
        mock_hash.return_value = "hashed_default"

        row = pd.Series({
            "username": "testuser",
            "password": "",
            "real_name": "测试用户",
            "email": "test@example.com"
        })

        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1, tenant_id=1
        )

        mock_hash.assert_called_with("123456")

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_with_roles(self, mock_hash):
        """测试创建带角色的用户"""
        mock_hash.return_value = "hashed"

        mock_role1 = MagicMock(spec=Role)
        mock_role1.id = 1
        mock_role2 = MagicMock(spec=Role)
        mock_role2.id = 2

        def get_role_side_effect(db, role_name, tenant_id):
            if role_name == "管理员":
                return mock_role1
            elif role_name == "普通用户":
                return mock_role2
            return None

        with patch.object(UserImportService, 'get_or_create_role', side_effect=get_role_side_effect):
            row = pd.Series({
                "username": "testuser",
                "real_name": "测试用户",
                "email": "test@example.com",
                "roles": "管理员,普通用户"
            })

            user = UserImportService.create_user_from_row(
                self.mock_db, row, operator_id=1, tenant_id=1
            )

            # 验证添加了2个角色
            self.assertEqual(self.mock_db.add.call_count, 3)  # 1 user + 2 user_roles

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_is_active_variants(self, mock_hash):
        """测试不同格式的 is_active 值"""
        mock_hash.return_value = "hashed"

        test_cases = [
            ("true", True),
            ("1", True),
            ("是", True),
            ("启用", True),
            ("false", False),
            ("0", False),
            (True, True),
            (False, False),
            (1, True),
            (0, False),
        ]

        for is_active_value, expected in test_cases:
            self.mock_db.reset_mock()

            row = pd.Series({
                "username": "testuser",
                "real_name": "测试用户",
                "email": "test@example.com",
                "is_active": is_active_value
            })

            user = UserImportService.create_user_from_row(
                self.mock_db, row, operator_id=1, tenant_id=1
            )

            self.assertEqual(user.is_active, expected, f"Failed for value: {is_active_value}")

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_optional_fields_none(self, mock_hash):
        """测试可选字段为空"""
        mock_hash.return_value = "hashed"

        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": pd.NA,
            "employee_no": pd.NA,
            "department": pd.NA,
            "position": pd.NA
        })

        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1, tenant_id=1
        )

        self.assertIsNone(user.phone)
        self.assertIsNone(user.employee_no)
        self.assertIsNone(user.department)
        self.assertIsNone(user.position)


class TestUserImportServiceImportUsers(unittest.TestCase):
    """批量导入用户测试"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch.object(UserImportService, 'create_user_from_row')
    @patch.object(UserImportService, 'validate_row')
    @patch.object(UserImportService, 'validate_dataframe')
    @patch.object(UserImportService, 'normalize_columns')
    def test_import_users_success(self, mock_normalize, mock_validate_df, mock_validate_row, mock_create_user):
        """测试成功导入所有用户"""
        df = pd.DataFrame({
            "username": ["user1", "user2"],
            "real_name": ["用户1", "用户2"],
            "email": ["user1@example.com", "user2@example.com"]
        })

        mock_normalize.return_value = df
        mock_validate_df.return_value = []
        mock_validate_row.return_value = None

        mock_user1 = MagicMock()
        mock_user1.username = "user1"
        mock_user1.real_name = "用户1"
        mock_user1.email = "user1@example.com"

        mock_user2 = MagicMock()
        mock_user2.username = "user2"
        mock_user2.real_name = "用户2"
        mock_user2.email = "user2@example.com"

        mock_create_user.side_effect = [mock_user1, mock_user2]

        # Mock query for validation
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1, tenant_id=1
        )

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(len(result["success_users"]), 2)
        self.mock_db.commit.assert_called_once()

    @patch.object(UserImportService, 'normalize_columns')
    @patch.object(UserImportService, 'validate_dataframe')
    def test_import_users_structure_validation_failed(self, mock_validate_df, mock_normalize):
        """测试结构验证失败"""
        df = pd.DataFrame({
            "username": ["user1"]
        })

        mock_normalize.return_value = df
        mock_validate_df.return_value = ["缺少必填列: real_name, email"]

        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1, tenant_id=1
        )

        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("缺少必填列", result["errors"][0])

    @patch.object(UserImportService, 'validate_row')
    @patch.object(UserImportService, 'validate_dataframe')
    @patch.object(UserImportService, 'normalize_columns')
    def test_import_users_row_validation_failed(self, mock_normalize, mock_validate_df, mock_validate_row):
        """测试行验证失败"""
        df = pd.DataFrame({
            "username": ["user1", "user2"],
            "real_name": ["用户1", "用户2"],
            "email": ["user1@example.com", "invalid-email"]
        })

        mock_normalize.return_value = df
        mock_validate_df.return_value = []
        mock_validate_row.side_effect = [None, "第3行: 邮箱格式不正确"]

        # Mock query for validation
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1, tenant_id=1
        )

        self.assertEqual(result["failed_count"], 2)
        self.assertGreater(len(result["errors"]), 0)

    @patch.object(UserImportService, 'create_user_from_row')
    @patch.object(UserImportService, 'validate_row')
    @patch.object(UserImportService, 'validate_dataframe')
    @patch.object(UserImportService, 'normalize_columns')
    def test_import_users_creation_exception_rollback(self, mock_normalize, mock_validate_df, mock_validate_row, mock_create_user):
        """测试创建用户异常时回滚"""
        df = pd.DataFrame({
            "username": ["user1"],
            "real_name": ["用户1"],
            "email": ["user1@example.com"]
        })

        mock_normalize.return_value = df
        mock_validate_df.return_value = []
        mock_validate_row.return_value = None
        mock_create_user.side_effect = Exception("Database error")

        # Mock query for validation
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1, tenant_id=1
        )

        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failed_count"], 1)
        self.mock_db.rollback.assert_called_once()
        self.assertGreater(len(result["errors"]), 0)


class TestUserImportServiceGenerateTemplate(unittest.TestCase):
    """生成导入模板测试"""

    def test_generate_template(self):
        """测试生成模板"""
        template = UserImportService.generate_template()

        self.assertIsInstance(template, pd.DataFrame)
        self.assertGreater(len(template), 0)

        # 验证必填列存在
        self.assertIn("用户名", template.columns)
        self.assertIn("真实姓名", template.columns)
        self.assertIn("邮箱", template.columns)

        # 验证可选列存在
        self.assertIn("密码", template.columns)
        self.assertIn("手机号", template.columns)
        self.assertIn("角色", template.columns)

    def test_generate_template_has_sample_data(self):
        """测试模板包含示例数据"""
        template = UserImportService.generate_template()

        self.assertGreater(len(template), 0)
        self.assertIsNotNone(template.iloc[0]["用户名"])
        self.assertIsNotNone(template.iloc[0]["真实姓名"])
        self.assertIsNotNone(template.iloc[0]["邮箱"])


class TestUserImportServiceEdgeCases(unittest.TestCase):
    """边界条件和异常情况测试"""

    def test_max_import_limit_constant(self):
        """测试最大导入限制常量"""
        self.assertEqual(UserImportService.MAX_IMPORT_LIMIT, 500)

    def test_required_fields_constant(self):
        """测试必填字段常量"""
        self.assertEqual(
            UserImportService.REQUIRED_FIELDS,
            ["username", "real_name", "email"]
        )

    def test_field_mapping_has_chinese_and_english(self):
        """测试字段映射包含中英文"""
        mapping = UserImportService.FIELD_MAPPING

        # 验证中文映射
        self.assertEqual(mapping["用户名"], "username")
        self.assertEqual(mapping["真实姓名"], "real_name")

        # 验证英文映射
        self.assertEqual(mapping["Username"], "username")
        self.assertEqual(mapping["Real Name"], "real_name")

    def test_validate_row_with_na_phone(self):
        """测试手机号为 NA 的情况"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com",
            "phone": pd.NA
        })

        error = UserImportService.validate_row(
            row, 2, mock_db, set(), set()
        )

        self.assertIsNone(error)

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_with_na_password(self, mock_hash):
        """测试密码为 NA 时使用默认密码"""
        mock_hash.return_value = "hashed"
        mock_db = MagicMock()

        row = pd.Series({
            "username": "testuser",
            "real_name": "测试",
            "email": "test@example.com",
            "password": pd.NA
        })

        user = UserImportService.create_user_from_row(
            mock_db, row, operator_id=1, tenant_id=1
        )

        mock_hash.assert_called_with("123456")


if __name__ == '__main__':
    unittest.main()
