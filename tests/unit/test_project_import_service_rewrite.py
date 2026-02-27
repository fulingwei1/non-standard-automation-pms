# -*- coding: utf-8 -*-
"""
项目导入服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（312行）
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import pandas as pd
from fastapi import HTTPException

from app.services.project_import_service import (
    validate_excel_file,
    parse_excel_data,
    validate_project_columns,
    get_column_value,
    parse_project_row,
    find_or_create_customer,
    find_project_manager,
    parse_date_value,
    parse_decimal_value,
    populate_project_from_row,
    import_projects_from_dataframe,
)
from app.models.project import Customer, Project
from app.models.user import User


class TestValidateExcelFile(unittest.TestCase):
    """测试Excel文件验证"""

    def test_validate_excel_file_xlsx(self):
        """测试.xlsx文件"""
        # 不应抛出异常
        validate_excel_file("test.xlsx")

    def test_validate_excel_file_xls(self):
        """测试.xls文件"""
        # 不应抛出异常
        validate_excel_file("test.xls")

    def test_validate_excel_file_invalid_extension(self):
        """测试无效文件扩展名"""
        with self.assertRaises(HTTPException) as context:
            validate_excel_file("test.csv")
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只支持Excel文件", context.exception.detail)

    def test_validate_excel_file_no_extension(self):
        """测试无扩展名文件"""
        with self.assertRaises(HTTPException) as context:
            validate_excel_file("test")
        self.assertEqual(context.exception.status_code, 400)


class TestParseExcelData(unittest.TestCase):
    """测试Excel解析"""

    @patch('app.services.project_import_service.ImportExportEngine.parse_excel')
    def test_parse_excel_data_success(self, mock_parse):
        """测试成功解析Excel"""
        mock_df = pd.DataFrame({
            '项目编码*': ['PRJ001', 'PRJ002'],
            '项目名称*': ['项目A', '项目B']
        })
        mock_parse.return_value = mock_df

        result = parse_excel_data(b'fake_content')

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        mock_parse.assert_called_once_with(b'fake_content')

    @patch('app.services.project_import_service.ImportExportEngine.parse_excel')
    def test_parse_excel_data_empty(self, mock_parse):
        """测试空文件"""
        mock_parse.return_value = pd.DataFrame()

        with self.assertRaises(HTTPException) as context:
            parse_excel_data(b'fake_content')

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("没有数据", context.exception.detail)

    @patch('app.services.project_import_service.ImportExportEngine.parse_excel')
    def test_parse_excel_data_parse_error(self, mock_parse):
        """测试解析错误"""
        mock_parse.side_effect = Exception("解析失败")

        with self.assertRaises(HTTPException) as context:
            parse_excel_data(b'fake_content')

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Excel文件解析失败", context.exception.detail)


class TestValidateProjectColumns(unittest.TestCase):
    """测试列验证"""

    def test_validate_columns_with_asterisk(self):
        """测试带*的列名"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['项目A']
        })
        # 不应抛出异常
        validate_project_columns(df)

    def test_validate_columns_without_asterisk(self):
        """测试不带*的列名"""
        df = pd.DataFrame({
            '项目编码': ['PRJ001'],
            '项目名称': ['项目A']
        })
        # 不应抛出异常
        validate_project_columns(df)

    def test_validate_columns_mixed(self):
        """测试混合列名"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称': ['项目A']
        })
        # 不应抛出异常
        validate_project_columns(df)

    def test_validate_columns_missing_code(self):
        """测试缺少项目编码列"""
        df = pd.DataFrame({
            '项目名称*': ['项目A']
        })
        with self.assertRaises(HTTPException) as context:
            validate_project_columns(df)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("项目编码*", context.exception.detail)

    def test_validate_columns_missing_name(self):
        """测试缺少项目名称列"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001']
        })
        with self.assertRaises(HTTPException) as context:
            validate_project_columns(df)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("项目名称*", context.exception.detail)

    def test_validate_columns_missing_both(self):
        """测试同时缺少必需列"""
        df = pd.DataFrame({
            '客户名称': ['客户A']
        })
        with self.assertRaises(HTTPException) as context:
            validate_project_columns(df)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("项目编码*", context.exception.detail)
        self.assertIn("项目名称*", context.exception.detail)


class TestGetColumnValue(unittest.TestCase):
    """测试列值获取"""

    def test_get_column_value_with_asterisk(self):
        """测试获取带*的列"""
        row = pd.Series({'项目编码*': 'PRJ001', '项目名称*': '项目A'})
        result = get_column_value(row, '项目编码*')
        self.assertEqual(result, 'PRJ001')

    def test_get_column_value_without_asterisk(self):
        """测试获取不带*的列"""
        row = pd.Series({'项目编码': 'PRJ001'})
        result = get_column_value(row, '项目编码*', '项目编码')
        self.assertEqual(result, 'PRJ001')

    def test_get_column_value_fallback(self):
        """测试回退到备用列名"""
        row = pd.Series({'项目编码': 'PRJ001'})
        result = get_column_value(row, '项目编码*')
        self.assertEqual(result, 'PRJ001')

    def test_get_column_value_none(self):
        """测试值为None"""
        row = pd.Series({'项目编码*': None})
        result = get_column_value(row, '项目编码*')
        self.assertIsNone(result)

    def test_get_column_value_nan(self):
        """测试值为NaN"""
        import numpy as np
        row = pd.Series({'项目编码*': np.nan})
        result = get_column_value(row, '项目编码*')
        self.assertIsNone(result)

    def test_get_column_value_empty_string(self):
        """测试空字符串"""
        row = pd.Series({'项目编码*': ''})
        result = get_column_value(row, '项目编码*')
        self.assertIsNone(result)

    def test_get_column_value_whitespace(self):
        """测试空白字符串"""
        row = pd.Series({'项目编码*': '  PRJ001  '})
        result = get_column_value(row, '项目编码*')
        self.assertEqual(result, 'PRJ001')

    def test_get_column_value_number(self):
        """测试数字值"""
        row = pd.Series({'金额': 1000})
        result = get_column_value(row, '金额')
        self.assertEqual(result, '1000')


class TestParseProjectRow(unittest.TestCase):
    """测试项目行解析"""

    def test_parse_project_row_success(self):
        """测试成功解析"""
        row = pd.Series({
            '项目编码*': 'PRJ001',
            '项目名称*': '项目A'
        })
        code, name, errors = parse_project_row(row, 0)

        self.assertEqual(code, 'PRJ001')
        self.assertEqual(name, '项目A')
        self.assertEqual(errors, [])

    def test_parse_project_row_missing_code(self):
        """测试缺少项目编码"""
        row = pd.Series({
            '项目编码*': None,
            '项目名称*': '项目A'
        })
        code, name, errors = parse_project_row(row, 0)

        self.assertIsNone(code)
        self.assertIsNone(name)
        self.assertEqual(len(errors), 1)
        self.assertIn("不能为空", errors[0])

    def test_parse_project_row_missing_name(self):
        """测试缺少项目名称"""
        row = pd.Series({
            '项目编码*': 'PRJ001',
            '项目名称*': None
        })
        code, name, errors = parse_project_row(row, 0)

        self.assertIsNone(code)
        self.assertIsNone(name)
        self.assertEqual(len(errors), 1)

    def test_parse_project_row_both_missing(self):
        """测试同时缺少"""
        row = pd.Series({
            '项目编码*': None,
            '项目名称*': ''
        })
        code, name, errors = parse_project_row(row, 5)

        self.assertIsNone(code)
        self.assertIsNone(name)
        self.assertTrue(len(errors) > 0)


class TestFindOrCreateCustomer(unittest.TestCase):
    """测试查找/创建客户"""

    def test_find_or_create_customer_exists(self):
        """测试查找已存在客户"""
        mock_db = MagicMock()
        mock_customer = Customer(id=1, customer_name='客户A')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

        result = find_or_create_customer(mock_db, '客户A')

        self.assertEqual(result, mock_customer)
        self.assertEqual(result.customer_name, '客户A')

    def test_find_or_create_customer_not_exists(self):
        """测试客户不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = find_or_create_customer(mock_db, '客户B')

        # 注意：当前实现只查找，不创建，返回None
        self.assertIsNone(result)

    def test_find_or_create_customer_empty_name(self):
        """测试空客户名"""
        mock_db = MagicMock()
        result = find_or_create_customer(mock_db, '')

        self.assertIsNone(result)
        mock_db.query.assert_not_called()

    def test_find_or_create_customer_none(self):
        """测试None客户名"""
        mock_db = MagicMock()
        result = find_or_create_customer(mock_db, None)

        self.assertIsNone(result)


class TestFindProjectManager(unittest.TestCase):
    """测试查找项目经理"""

    def test_find_project_manager_by_real_name(self):
        """测试按真实姓名查找"""
        mock_db = MagicMock()
        mock_user = User(id=1, username='zhangsan', real_name='张三',
        password_hash="test_hash_123"
    )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = find_project_manager(mock_db, '张三')

        self.assertEqual(result, mock_user)
        self.assertEqual(result.real_name, '张三')

    def test_find_project_manager_by_username(self):
        """测试按用户名查找（real_name不匹配时）"""
        mock_db = MagicMock()
        mock_user = User(id=1, username='zhangsan', real_name='张三',
        password_hash="test_hash_123"
    )
        
        # 第一次按real_name查找返回None，第二次按username查找返回user
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_user]

        result = find_project_manager(mock_db, 'zhangsan')

        self.assertEqual(result, mock_user)

    def test_find_project_manager_not_found(self):
        """测试找不到项目经理"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = find_project_manager(mock_db, '不存在的人')

        self.assertIsNone(result)

    def test_find_project_manager_empty(self):
        """测试空名称"""
        mock_db = MagicMock()
        result = find_project_manager(mock_db, '')

        self.assertIsNone(result)

    def test_find_project_manager_none(self):
        """测试None"""
        mock_db = MagicMock()
        result = find_project_manager(mock_db, None)

        self.assertIsNone(result)


class TestParseDateValue(unittest.TestCase):
    """测试日期解析"""

    def test_parse_date_value_string(self):
        """测试字符串日期"""
        result = parse_date_value('2024-01-15')
        self.assertEqual(result, date(2024, 1, 15))

    def test_parse_date_value_datetime(self):
        """测试datetime对象"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = parse_date_value(dt)
        self.assertEqual(result, date(2024, 1, 15))

    def test_parse_date_value_timestamp(self):
        """测试Pandas Timestamp"""
        ts = pd.Timestamp('2024-01-15')
        result = parse_date_value(ts)
        self.assertEqual(result, date(2024, 1, 15))

    def test_parse_date_value_none(self):
        """测试None"""
        result = parse_date_value(None)
        self.assertIsNone(result)

    def test_parse_date_value_na(self):
        """测试pd.NA"""
        result = parse_date_value(pd.NA)
        self.assertIsNone(result)

    def test_parse_date_value_invalid(self):
        """测试无效日期"""
        result = parse_date_value('invalid-date')
        self.assertIsNone(result)

    def test_parse_date_value_number(self):
        """测试数字（可能是Excel日期序列）"""
        # Excel日期序列（从1900-01-01开始的天数）
        result = parse_date_value(45000)
        # 应该能转换为某个日期
        self.assertIsNotNone(result)


class TestParseDecimalValue(unittest.TestCase):
    """测试金额解析"""

    def test_parse_decimal_value_integer(self):
        """测试整数"""
        result = parse_decimal_value(1000)
        self.assertEqual(result, Decimal('1000'))

    def test_parse_decimal_value_float(self):
        """测试浮点数"""
        result = parse_decimal_value(1000.50)
        self.assertEqual(result, Decimal('1000.50'))

    def test_parse_decimal_value_string(self):
        """测试字符串"""
        result = parse_decimal_value('1000.50')
        self.assertEqual(result, Decimal('1000.50'))

    def test_parse_decimal_value_none(self):
        """测试None"""
        result = parse_decimal_value(None)
        self.assertIsNone(result)

    def test_parse_decimal_value_na(self):
        """测试pd.NA"""
        result = parse_decimal_value(pd.NA)
        self.assertIsNone(result)

    def test_parse_decimal_value_invalid(self):
        """测试无效值"""
        result = parse_decimal_value('invalid')
        self.assertIsNone(result)

    def test_parse_decimal_value_empty_string(self):
        """测试空字符串"""
        result = parse_decimal_value('')
        self.assertIsNone(result)


class TestPopulateProjectFromRow(unittest.TestCase):
    """测试项目信息填充"""

    def setUp(self):
        """设置测试"""
        self.mock_db = MagicMock()
        self.project = Project(
            project_code='PRJ001',
            project_name='测试项目'
        )

    def test_populate_with_customer(self):
        """测试填充客户信息"""
        row = pd.Series({
            '客户名称': '客户A'
        })
        mock_customer = Customer(
            id=1,
            customer_name='客户A',
            contact_person='联系人A',
            contact_phone='13800138000'
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.customer_id, 1)
        self.assertEqual(self.project.customer_name, '客户A')
        self.assertEqual(self.project.customer_contact, '联系人A')
        self.assertEqual(self.project.customer_phone, '13800138000')

    def test_populate_with_contract_info(self):
        """测试填充合同信息"""
        row = pd.Series({
            '合同编号': 'HT2024001',
            '项目类型': '开发项目',
            '合同日期': '2024-01-15',
            '合同金额': 100000,
            '预算金额': 90000
        })

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.contract_no, 'HT2024001')
        self.assertEqual(self.project.project_type, '开发项目')
        self.assertEqual(self.project.contract_date, date(2024, 1, 15))
        self.assertEqual(self.project.contract_amount, Decimal('100000'))
        self.assertEqual(self.project.budget_amount, Decimal('90000'))

    def test_populate_with_dates(self):
        """测试填充日期"""
        row = pd.Series({
            '计划开始日期': '2024-02-01',
            '计划结束日期': '2024-06-30'
        })

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.planned_start_date, date(2024, 2, 1))
        self.assertEqual(self.project.planned_end_date, date(2024, 6, 30))

    def test_populate_with_project_manager(self):
        """测试填充项目经理"""
        row = pd.Series({
            '项目经理': '张三'
        })
        mock_user = User(id=1, username='zhangsan', real_name='张三',
        password_hash="test_hash_123"
    )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.pm_id, 1)
        self.assertEqual(self.project.pm_name, '张三')

    def test_populate_with_description(self):
        """测试填充项目描述"""
        row = pd.Series({
            '项目描述': '这是一个测试项目'
        })

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.description, '这是一个测试项目')

    def test_populate_with_empty_row(self):
        """测试空行"""
        row = pd.Series({})

        # 不应抛出异常
        populate_project_from_row(self.mock_db, self.project, row)

    def test_populate_with_none_values(self):
        """测试包含None值的行"""
        row = pd.Series({
            '客户名称': None,
            '合同编号': None,
            '项目经理': None
        })

        # 不应抛出异常
        populate_project_from_row(self.mock_db, self.project, row)

    def test_populate_pm_with_username_only(self):
        """测试项目经理只有username"""
        row = pd.Series({
            '项目经理': '张三'
        })
        mock_user = User(id=1, username='zhangsan', real_name=None,
        password_hash="test_hash_123"
    )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        populate_project_from_row(self.mock_db, self.project, row)

        self.assertEqual(self.project.pm_id, 1)
        self.assertEqual(self.project.pm_name, 'zhangsan')


class TestImportProjectsFromDataframe(unittest.TestCase):
    """测试从DataFrame导入项目"""

    def setUp(self):
        """设置测试"""
        self.mock_db = MagicMock()

    @patch('app.services.project_import_service.init_project_stages')
    def test_import_new_project(self, mock_init_stages):
        """测试导入新项目"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['测试项目']
        })

        # 模拟项目不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=False
        )

        self.assertEqual(imported, 1)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 0)
        self.mock_db.add.assert_called_once()
        self.mock_db.flush.assert_called_once()
        mock_init_stages.assert_called_once()

    def test_import_duplicate_project_no_update(self):
        """测试导入重复项目（不更新）"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['测试项目']
        })

        # 模拟项目已存在
        existing = Project(id=1, project_code='PRJ001')
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=False
        )

        self.assertEqual(imported, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 1)
        self.assertIn('已存在', failed[0]['error'])

    def test_import_duplicate_project_with_update(self):
        """测试导入重复项目（更新）"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['测试项目更新']
        })

        # 模拟项目已存在
        existing = Project(id=1, project_code='PRJ001', project_name='旧名称')
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=True
        )

        self.assertEqual(imported, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(len(failed), 0)

    def test_import_multiple_projects(self):
        """测试导入多个项目"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001', 'PRJ002', 'PRJ003'],
            '项目名称*': ['项目A', '项目B', '项目C']
        })

        # 模拟所有项目不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.project_import_service.init_project_stages'):
            imported, updated, failed = import_projects_from_dataframe(
                self.mock_db, df, update_existing=False
            )

        self.assertEqual(imported, 3)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 0)

    def test_import_with_invalid_rows(self):
        """测试包含无效行的导入"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001', None, 'PRJ003'],
            '项目名称*': ['项目A', '项目B', None]
        })

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.project_import_service.init_project_stages'):
            imported, updated, failed = import_projects_from_dataframe(
                self.mock_db, df, update_existing=False
            )

        self.assertEqual(imported, 1)  # 只有PRJ001成功
        self.assertEqual(len(failed), 2)  # 两行失败

    def test_import_with_exception(self):
        """测试导入过程中发生异常"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['测试项目']
        })

        # 模拟数据库操作抛出异常
        self.mock_db.query.side_effect = Exception("数据库错误")

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=False
        )

        self.assertEqual(imported, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("数据库错误", failed[0]['error'])

    @patch('app.services.project_import_service.init_project_stages')
    def test_import_with_full_data(self, mock_init_stages):
        """测试导入完整数据"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001'],
            '项目名称*': ['完整项目'],
            '客户名称': ['客户A'],
            '合同编号': ['HT001'],
            '项目类型': ['开发'],
            '合同金额': [100000],
            '项目经理': ['张三']
        })

        # 模拟查询返回
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=False
        )

        self.assertEqual(imported, 1)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 0)

    def test_import_empty_dataframe(self):
        """测试导入空DataFrame"""
        df = pd.DataFrame({
            '项目编码*': [],
            '项目名称*': []
        })

        imported, updated, failed = import_projects_from_dataframe(
            self.mock_db, df, update_existing=False
        )

        self.assertEqual(imported, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 0)

    def test_import_mixed_success_and_failure(self):
        """测试混合成功和失败的情况"""
        df = pd.DataFrame({
            '项目编码*': ['PRJ001', 'PRJ002', None, 'PRJ004'],
            '项目名称*': ['项目A', '项目B', '项目C', '项目D']
        })

        # PRJ002已存在
        def mock_query_side_effect(*args):
            mock_result = MagicMock()
            def filter_func(*args):
                mock_filter = MagicMock()
                # 根据调用次数返回不同结果
                if not hasattr(mock_query_side_effect, 'call_count'):
                    mock_query_side_effect.call_count = 0
                mock_query_side_effect.call_count += 1
                
                if mock_query_side_effect.call_count == 2:  # PRJ002
                    mock_filter.first.return_value = Project(id=2, project_code='PRJ002')
                else:
                    mock_filter.first.return_value = None
                return mock_filter
            mock_result.filter = filter_func
            return mock_result

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch('app.services.project_import_service.init_project_stages'):
            imported, updated, failed = import_projects_from_dataframe(
                self.mock_db, df, update_existing=False
            )

        # PRJ001成功，PRJ002已存在失败，第3行缺少编码失败，PRJ004成功
        self.assertEqual(imported, 2)
        self.assertEqual(updated, 0)
        self.assertEqual(len(failed), 2)


if __name__ == "__main__":
    unittest.main()
