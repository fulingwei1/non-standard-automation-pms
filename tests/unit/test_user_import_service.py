# -*- coding: utf-8 -*-
"""
用户导入服务单元测试

目标：
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import io
import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime

import pandas as pd

from app.services.user_import_service import UserImportService


class TestUserImportServiceValidation(unittest.TestCase):
    """测试验证相关方法"""

    def test_validate_file_format_xlsx(self):
        """测试XLSX文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.xlsx"))
        self.assertTrue(UserImportService.validate_file_format("USERS.XLSX"))

    def test_validate_file_format_xls(self):
        """测试XLS文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.xls"))
        self.assertTrue(UserImportService.validate_file_format("USERS.XLS"))

    def test_validate_file_format_csv(self):
        """测试CSV文件格式验证"""
        self.assertTrue(UserImportService.validate_file_format("users.csv"))
        self.assertTrue(UserImportService.validate_file_format("USERS.CSV"))

    def test_validate_file_format_invalid(self):
        """测试无效文件格式"""
        self.assertFalse(UserImportService.validate_file_format("users.txt"))
        self.assertFalse(UserImportService.validate_file_format("users.doc"))
        self.assertFalse(UserImportService.validate_file_format("users.pdf"))

    def test_normalize_columns_chinese(self):
        """测试中文列名标准化"""
        df = pd.DataFrame({
            "用户名": ["test"],
            "真实姓名": ["测试"],
            "邮箱": ["test@example.com"]
        })
        result = UserImportService.normalize_columns(df)
        self.assertIn("username", result.columns)
        self.assertIn("real_name", result.columns)
        self.assertIn("email", result.columns)

    def test_normalize_columns_english(self):
        """测试英文列名标准化"""
        df = pd.DataFrame({
            "Username": ["test"],
            "Real Name": ["Test User"],
            "Email": ["test@example.com"]
        })
        result = UserImportService.normalize_columns(df)
        self.assertIn("username", result.columns)
        self.assertIn("real_name", result.columns)
        self.assertIn("email", result.columns)

    def test_normalize_columns_mixed(self):
        """测试中英文混合列名"""
        df = pd.DataFrame({
            "用户名": ["test"],
            "Real Name": ["Test User"],
            "邮箱": ["test@example.com"],
            "custom_field": ["value"]
        })
        result = UserImportService.normalize_columns(df)
        self.assertIn("username", result.columns)
        self.assertIn("real_name", result.columns)
        self.assertIn("email", result.columns)
        self.assertIn("custom_field", result.columns)  # 未映射的列保留

    def test_validate_dataframe_success(self):
        """测试DataFrame结构验证成功"""
        df = pd.DataFrame({
            "username": ["test1", "test2"],
            "real_name": ["用户1", "用户2"],
            "email": ["test1@example.com", "test2@example.com"]
        })
        errors = UserImportService.validate_dataframe(df)
        self.assertEqual(errors, [])

    def test_validate_dataframe_missing_fields(self):
        """测试缺少必填字段"""
        df = pd.DataFrame({
            "username": ["test1"],
            "real_name": ["用户1"]
            # 缺少 email
        })
        errors = UserImportService.validate_dataframe(df)
        self.assertEqual(len(errors), 1)
        self.assertIn("email", errors[0])

    def test_validate_dataframe_empty(self):
        """测试空DataFrame"""
        df = pd.DataFrame({
            "username": [],
            "real_name": [],
            "email": []
        })
        errors = UserImportService.validate_dataframe(df)
        self.assertEqual(len(errors), 1)
        self.assertIn("没有数据", errors[0])

    def test_validate_dataframe_exceed_limit(self):
        """测试超过最大导入数量"""
        # 创建超过限制的数据
        data = {
            "username": [f"user{i}" for i in range(501)],
            "real_name": [f"用户{i}" for i in range(501)],
            "email": [f"user{i}@example.com" for i in range(501)]
        }
        df = pd.DataFrame(data)
        errors = UserImportService.validate_dataframe(df)
        self.assertEqual(len(errors), 1)
        self.assertIn("不能超过", errors[0])
        self.assertIn("501", errors[0])


class TestUserImportServiceRowValidation(unittest.TestCase):
    """测试单行数据验证"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.existing_usernames = set()
        self.existing_emails = set()

    def test_validate_row_success(self):
        """测试有效行验证通过"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000"
        })
        
        # Mock数据库查询返回None（用户不存在）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db, 
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNone(error)

    def test_validate_row_missing_username(self):
        """测试缺少用户名"""
        row = pd.Series({
            "username": "",
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("username", error)

    def test_validate_row_missing_real_name(self):
        """测试缺少真实姓名"""
        row = pd.Series({
            "username": "testuser",
            "real_name": None,
            "email": "test@example.com"
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("real_name", error)

    def test_validate_row_missing_email(self):
        """测试缺少邮箱"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": ""
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("email", error)

    def test_validate_row_username_too_short(self):
        """测试用户名过短"""
        row = pd.Series({
            "username": "ab",  # 只有2个字符
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("长度", error)

    def test_validate_row_username_too_long(self):
        """测试用户名过长"""
        row = pd.Series({
            "username": "a" * 51,  # 51个字符
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("长度", error)

    def test_validate_row_duplicate_username_in_file(self):
        """测试文件内用户名重复"""
        self.existing_usernames.add("testuser")
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("重复", error)
        self.assertIn("testuser", error)

    def test_validate_row_username_exists_in_db(self):
        """测试用户名在数据库中已存在"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        
        # Mock数据库查询返回已存在的用户
        mock_user = MagicMock()
        mock_user.username = "testuser"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("已存在", error)

    def test_validate_row_invalid_email_format(self):
        """测试邮箱格式不正确"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "invalid-email"
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("邮箱", error)

    def test_validate_row_duplicate_email_in_file(self):
        """测试文件内邮箱重复"""
        self.existing_emails.add("test@example.com")
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com"
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("邮箱", error)
        self.assertIn("重复", error)

    def test_validate_row_invalid_phone_format(self):
        """测试手机号格式不正确"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "123"  # 太短
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNotNone(error)
        self.assertIn("手机号", error)

    def test_validate_row_phone_optional(self):
        """测试手机号可选"""
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com"
            # 没有phone字段
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            self.existing_usernames, self.existing_emails
        )
        self.assertIsNone(error)


class TestUserImportServiceRoleManagement(unittest.TestCase):
    """测试角色管理"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()

    def test_get_or_create_role_exists(self):
        """测试获取已存在的角色"""
        mock_role = MagicMock()
        mock_role.role_name = "普通用户"
        mock_role.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_role
        
        role = UserImportService.get_or_create_role(self.mock_db, "普通用户")
        
        self.assertIsNotNone(role)
        self.assertEqual(role.role_name, "普通用户")

    def test_get_or_create_role_not_exists(self):
        """测试角色不存在的情况"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        role = UserImportService.get_or_create_role(self.mock_db, "不存在的角色")
        
        self.assertIsNone(role)

    def test_get_or_create_role_with_tenant(self):
        """测试带租户ID的角色查询"""
        mock_role = MagicMock()
        mock_role.role_name = "管理员"
        mock_role.tenant_id = 10
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_role
        
        role = UserImportService.get_or_create_role(self.mock_db, "管理员", tenant_id=10)
        
        self.assertIsNotNone(role)
        self.assertEqual(role.tenant_id, 10)


class TestUserImportServiceUserCreation(unittest.TestCase):
    """测试用户创建"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_basic(self, mock_hash):
        """测试基本用户创建"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "password": "123456"
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        # 验证db.add和db.flush被调用
        self.mock_db.add.assert_called_once()
        self.mock_db.flush.assert_called_once()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_default_password(self, mock_hash):
        """测试使用默认密码"""
        mock_hash.return_value = "hashed_default_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com"
            # 没有password字段
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        # 验证使用默认密码 "123456"
        mock_hash.assert_called_once_with("123456")

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_with_phone(self, mock_hash):
        """测试创建带手机号的用户"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000"
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        self.mock_db.add.assert_called_once()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_with_optional_fields(self, mock_hash):
        """测试创建带所有可选字段的用户"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000",
            "employee_no": "EMP001",
            "department": "技术部",
            "position": "工程师"
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1, tenant_id=10
        )
        
        self.mock_db.add.assert_called()
        self.mock_db.flush.assert_called()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_is_active_true(self, mock_hash):
        """测试is_active为True的各种格式"""
        mock_hash.return_value = "hashed_password"
        
        test_cases = [
            "true",
            "True",
            "1",
            "是",
            "启用",
            True,
            1
        ]
        
        for is_active_value in test_cases:
            row = pd.Series({
                "username": "testuser",
                "real_name": "测试用户",
                "email": "test@example.com",
                "is_active": is_active_value
            })
            
            user = UserImportService.create_user_from_row(
                self.mock_db, row, operator_id=1
            )
            
            self.mock_db.add.assert_called()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_is_active_false(self, mock_hash):
        """测试is_active为False"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "is_active": "false"
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        self.mock_db.add.assert_called()

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_with_roles(self, mock_hash):
        """测试创建带角色的用户"""
        mock_hash.return_value = "hashed_password"
        
        # Mock角色查询
        mock_role1 = MagicMock()
        mock_role1.id = 1
        mock_role1.role_name = "普通用户"
        
        mock_role2 = MagicMock()
        mock_role2.id = 2
        mock_role2.role_name = "销售经理"
        
        def get_role_side_effect(*args, **kwargs):
            role_name = args[1]
            if role_name == "普通用户":
                return mock_role1
            elif role_name == "销售经理":
                return mock_role2
            return None
        
        with patch.object(UserImportService, 'get_or_create_role', side_effect=get_role_side_effect):
            row = pd.Series({
                "username": "testuser",
                "real_name": "测试用户",
                "email": "test@example.com",
                "roles": "普通用户,销售经理"
            })
            
            user = UserImportService.create_user_from_row(
                self.mock_db, row, operator_id=1
            )
            
            # 验证db.add被调用了3次（1次用户 + 2次角色关联）
            self.assertEqual(self.mock_db.add.call_count, 3)

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_from_row_with_invalid_role(self, mock_hash):
        """测试带无效角色的用户创建"""
        mock_hash.return_value = "hashed_password"
        
        with patch.object(UserImportService, 'get_or_create_role', return_value=None):
            row = pd.Series({
                "username": "testuser",
                "real_name": "测试用户",
                "email": "test@example.com",
                "roles": "不存在的角色"
            })
            
            user = UserImportService.create_user_from_row(
                self.mock_db, row, operator_id=1
            )
            
            # 验证用户仍然被创建，只是没有角色
            self.mock_db.add.assert_called()


class TestUserImportServiceBatchImport(unittest.TestCase):
    """测试批量导入"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()

    @patch('app.services.user_import_service.get_password_hash')
    def test_import_users_success(self, mock_hash):
        """测试成功导入用户"""
        mock_hash.return_value = "hashed_password"
        
        df = pd.DataFrame({
            "username": ["user1", "user2"],
            "real_name": ["用户1", "用户2"],
            "email": ["user1@example.com", "user2@example.com"]
        })
        
        # Mock数据库查询返回None（用户不存在）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1
        )
        
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(len(result["success_users"]), 2)
        
        # 验证commit被调用
        self.mock_db.commit.assert_called_once()

    def test_import_users_validation_error(self):
        """测试导入时验证失败"""
        df = pd.DataFrame({
            "username": ["user1"],
            "real_name": ["用户1"]
            # 缺少email字段
        })
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1
        )
        
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failed_count"], 1)
        self.assertGreater(len(result["errors"]), 0)
        
        # 验证commit没有被调用
        self.mock_db.commit.assert_not_called()

    @patch('app.services.user_import_service.get_password_hash')
    def test_import_users_duplicate_in_file(self, mock_hash):
        """测试文件内重复数据"""
        mock_hash.return_value = "hashed_password"
        
        df = pd.DataFrame({
            "username": ["user1", "user1"],  # 重复的用户名
            "real_name": ["用户1", "用户2"],
            "email": ["user1@example.com", "user2@example.com"]
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1
        )
        
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failed_count"], 2)
        self.assertGreater(len(result["errors"]), 0)

    @patch('app.services.user_import_service.get_password_hash')
    def test_import_users_exception_rollback(self, mock_hash):
        """测试异常时回滚"""
        mock_hash.return_value = "hashed_password"
        
        df = pd.DataFrame({
            "username": ["user1"],
            "real_name": ["用户1"],
            "email": ["user1@example.com"]
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock db.flush抛出异常
        self.mock_db.flush.side_effect = Exception("数据库错误")
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1
        )
        
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failed_count"], 1)
        
        # 验证rollback被调用
        self.mock_db.rollback.assert_called_once()

    @patch('app.services.user_import_service.get_password_hash')
    def test_import_users_with_tenant(self, mock_hash):
        """测试带租户ID的导入"""
        mock_hash.return_value = "hashed_password"
        
        df = pd.DataFrame({
            "username": ["user1"],
            "real_name": ["用户1"],
            "email": ["user1@example.com"]
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1, tenant_id=10
        )
        
        self.assertEqual(result["success_count"], 1)

    def test_import_users_empty_dataframe(self):
        """测试空DataFrame导入"""
        df = pd.DataFrame({
            "username": [],
            "real_name": [],
            "email": []
        })
        
        result = UserImportService.import_users(
            self.mock_db, df, operator_id=1
        )
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["failed_count"], 0)
        self.assertGreater(len(result["errors"]), 0)


class TestUserImportServiceFileReading(unittest.TestCase):
    """测试文件读取"""

    @patch('pandas.read_excel')
    def test_read_file_xlsx(self, mock_read_excel):
        """测试读取XLSX文件"""
        mock_df = pd.DataFrame({
            "Username": ["test1"],
            "Email": ["test1@example.com"]
        })
        mock_read_excel.return_value = mock_df
        
        result = UserImportService.read_file("test.xlsx")
        
        mock_read_excel.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_csv')
    def test_read_file_csv(self, mock_read_csv):
        """测试读取CSV文件"""
        mock_df = pd.DataFrame({
            "Username": ["test1"],
            "Email": ["test1@example.com"]
        })
        mock_read_csv.return_value = mock_df
        
        result = UserImportService.read_file("test.csv")
        
        mock_read_csv.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_excel')
    def test_read_file_with_content(self, mock_read_excel):
        """测试通过字节流读取文件"""
        mock_df = pd.DataFrame({
            "Username": ["test1"],
            "Email": ["test1@example.com"]
        })
        mock_read_excel.return_value = mock_df
        
        file_content = b"fake excel content"
        result = UserImportService.read_file("test.xlsx", file_content=file_content)
        
        mock_read_excel.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_excel')
    def test_read_file_exception(self, mock_read_excel):
        """测试文件读取异常"""
        mock_read_excel.side_effect = Exception("文件损坏")
        
        with self.assertRaises(ValueError) as context:
            UserImportService.read_file("test.xlsx")
        
        self.assertIn("文件读取失败", str(context.exception))


class TestUserImportServiceTemplate(unittest.TestCase):
    """测试模板生成"""

    def test_generate_template(self):
        """测试生成导入模板"""
        template = UserImportService.generate_template()
        
        self.assertIsInstance(template, pd.DataFrame)
        self.assertEqual(len(template), 3)  # 3行示例数据
        
        # 验证列名
        expected_columns = [
            "用户名", "密码", "真实姓名", "邮箱", "手机号",
            "工号", "部门", "职位", "角色", "是否启用"
        ]
        for col in expected_columns:
            self.assertIn(col, template.columns)
        
        # 验证示例数据
        self.assertEqual(template["用户名"].iloc[0], "zhangsan")
        self.assertEqual(template["真实姓名"].iloc[0], "张三")
        self.assertIn("@example.com", template["邮箱"].iloc[0])


class TestUserImportServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()

    def test_validate_row_with_nan_values(self):
        """测试NaN值处理"""
        import numpy as np
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": np.nan,  # NaN值
            "employee_no": np.nan
        })
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        error = UserImportService.validate_row(
            row, 2, self.mock_db,
            set(), set()
        )
        self.assertIsNone(error)

    def test_normalize_columns_no_mapping_needed(self):
        """测试不需要映射的列名"""
        df = pd.DataFrame({
            "custom1": ["value1"],
            "custom2": ["value2"]
        })
        
        result = UserImportService.normalize_columns(df)
        
        # 列名应保持不变
        self.assertIn("custom1", result.columns)
        self.assertIn("custom2", result.columns)

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_empty_password(self, mock_hash):
        """测试空密码使用默认值"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "password": ""  # 空密码
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        # 应该使用默认密码
        mock_hash.assert_called_once_with("123456")

    @patch('app.services.user_import_service.get_password_hash')
    def test_create_user_whitespace_only_fields(self, mock_hash):
        """测试只包含空白字符的字段"""
        mock_hash.return_value = "hashed_password"
        
        row = pd.Series({
            "username": "testuser",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "   ",  # 只有空格
            "department": "  "
        })
        
        user = UserImportService.create_user_from_row(
            self.mock_db, row, operator_id=1
        )
        
        self.mock_db.add.assert_called()

    def test_validate_dataframe_all_required_fields(self):
        """测试所有必填字段都存在"""
        df = pd.DataFrame({
            "username": ["test"],
            "real_name": ["测试"],
            "email": ["test@example.com"],
            "extra_field": ["extra"]
        })
        
        errors = UserImportService.validate_dataframe(df)
        self.assertEqual(errors, [])

    @patch('app.services.user_import_service.get_password_hash')
    def test_import_users_with_roles_partial_success(self, mock_hash):
        """测试部分角色不存在的情况"""
        mock_hash.return_value = "hashed_password"
        
        df = pd.DataFrame({
            "username": ["user1"],
            "real_name": ["用户1"],
            "email": ["user1@example.com"],
            "roles": "存在的角色,不存在的角色"
        })
        
        mock_role = MagicMock()
        mock_role.id = 1
        
        def get_role_side_effect(*args, **kwargs):
            role_name = args[1]
            if role_name == "存在的角色":
                return mock_role
            return None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(UserImportService, 'get_or_create_role', side_effect=get_role_side_effect):
            result = UserImportService.import_users(
                self.mock_db, df, operator_id=1
            )
            
            # 用户应该成功创建，只是部分角色未分配
            self.assertEqual(result["success_count"], 1)


if __name__ == "__main__":
    unittest.main()
