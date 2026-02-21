# -*- coding: utf-8 -*-
"""
HR档案导入服务增强测试
"""

import unittest
from datetime import datetime
from decimal import Decimal, InvalidOperation
from unittest.mock import MagicMock, patch, Mock

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.hr_profile_import_service import (
    clean_str,
    clean_phone,
    parse_date,
    clean_decimal,
    validate_excel_file,
    validate_required_columns,
    get_existing_employees,
    generate_employee_code,
    build_department_name,
    determine_employment_status,
    determine_employment_type,
    create_or_update_employee,
    update_hr_profile_from_row,
    process_hr_profile_row,
    import_hr_profiles_from_dataframe,
)


class TestCleanStr(unittest.TestCase):
    """测试 clean_str 函数"""

    def test_clean_str_normal(self):
        """测试正常字符串"""
        assert clean_str("张三") == "张三"

    def test_clean_str_with_newline(self):
        """测试包含换行符的字符串"""
        assert clean_str("张三\n") == "张三"

    def test_clean_str_with_spaces(self):
        """测试包含空格的字符串"""
        assert clean_str("  张三  ") == "张三"

    def test_clean_str_with_slash(self):
        """测试斜杠值"""
        assert clean_str("/") is None

    def test_clean_str_nan_string(self):
        """测试NaN字符串"""
        assert clean_str("NaN") is None

    def test_clean_str_empty(self):
        """测试空字符串"""
        assert clean_str("") is None

    def test_clean_str_pandas_na(self):
        """测试pandas NA值"""
        assert clean_str(pd.NA) is None

    def test_clean_str_none(self):
        """测试None值"""
        assert clean_str(None) is None


class TestCleanPhone(unittest.TestCase):
    """测试 clean_phone 函数"""

    def test_clean_phone_normal(self):
        """测试正常电话号码"""
        assert clean_phone("13800138000") == "13800138000"

    def test_clean_phone_scientific_notation(self):
        """测试科学计数法格式"""
        assert clean_phone("1.38e+10") == "13800000000"

    def test_clean_phone_with_decimal(self):
        """测试带小数点的电话"""
        assert clean_phone("13800138000.0") == "13800138000"

    def test_clean_phone_pandas_na(self):
        """测试pandas NA值"""
        assert clean_phone(pd.NA) is None

    def test_clean_phone_empty_string(self):
        """测试空字符串"""
        assert clean_phone("") is None

    def test_clean_phone_with_spaces(self):
        """测试带空格的电话"""
        assert clean_phone("  13800138000  ") == "13800138000"

    def test_clean_phone_invalid_conversion(self):
        """测试无效转换"""
        result = clean_phone("invalid")
        assert result == "invalid"


class TestParseDate(unittest.TestCase):
    """测试 parse_date 函数"""

    def test_parse_date_datetime_object(self):
        """测试datetime对象"""
        dt = datetime(2024, 1, 15, 10, 30)
        result = parse_date(dt)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_string_hyphen(self):
        """测试连字符格式日期字符串"""
        result = parse_date("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_string_slash(self):
        """测试斜杠格式日期字符串"""
        result = parse_date("2024/01/15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_invalid_format(self):
        """测试无效日期格式"""
        assert parse_date("2024-13-45") is None
        assert parse_date("invalid") is None

    def test_parse_date_pandas_na(self):
        """测试pandas NA值"""
        assert parse_date(pd.NA) is None

    def test_parse_date_none(self):
        """测试None值"""
        assert parse_date(None) is None


class TestCleanDecimal(unittest.TestCase):
    """测试 clean_decimal 函数"""

    def test_clean_decimal_integer(self):
        """测试整数"""
        assert clean_decimal(100) == Decimal("100")

    def test_clean_decimal_float(self):
        """测试浮点数"""
        assert clean_decimal(100.5) == Decimal("100.5")

    def test_clean_decimal_string(self):
        """测试数字字符串"""
        assert clean_decimal("100.5") == Decimal("100.5")

    def test_clean_decimal_pandas_na(self):
        """测试pandas NA值"""
        assert clean_decimal(pd.NA) is None

    def test_clean_decimal_invalid(self):
        """测试无效值"""
        assert clean_decimal("invalid") is None

    def test_clean_decimal_none(self):
        """测试None值"""
        assert clean_decimal(None) is None


class TestValidateExcelFile(unittest.TestCase):
    """测试 validate_excel_file 函数"""

    def test_validate_excel_file_xlsx(self):
        """测试.xlsx文件"""
        validate_excel_file("test.xlsx")  # 不应抛出异常

    def test_validate_excel_file_xls(self):
        """测试.xls文件"""
        validate_excel_file("test.xls")  # 不应抛出异常

    def test_validate_excel_file_invalid(self):
        """测试无效文件类型"""
        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("test.csv")
        assert exc_info.value.status_code == 400
        assert "Excel文件" in exc_info.value.detail

    def test_validate_excel_file_no_extension(self):
        """测试无扩展名文件"""
        with pytest.raises(HTTPException):
            validate_excel_file("test")


class TestValidateRequiredColumns(unittest.TestCase):
    """测试 validate_required_columns 函数"""

    def test_validate_required_columns_valid(self):
        """测试包含必需列"""
        df = pd.DataFrame({"姓名": ["张三"], "部门": ["技术部"]})
        validate_required_columns(df)  # 不应抛出异常

    def test_validate_required_columns_missing(self):
        """测试缺少必需列"""
        df = pd.DataFrame({"部门": ["技术部"]})
        with pytest.raises(HTTPException) as exc_info:
            validate_required_columns(df)
        assert exc_info.value.status_code == 400
        assert "姓名" in exc_info.value.detail


class TestGetExistingEmployees(unittest.TestCase):
    """测试 get_existing_employees 函数"""

    def test_get_existing_employees_empty(self):
        """测试空数据库"""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        name_to_employee, existing_codes = get_existing_employees(mock_db)

        assert name_to_employee == {}
        assert existing_codes == set()

    def test_get_existing_employees_with_data(self):
        """测试有数据的情况"""
        mock_db = MagicMock()
        mock_employee1 = MagicMock()
        mock_employee1.name = "张三"
        mock_employee1.employee_code = "EMP-00001"

        mock_employee2 = MagicMock()
        mock_employee2.name = "李四"
        mock_employee2.employee_code = "EMP-00002"

        mock_db.query.return_value.all.return_value = [mock_employee1, mock_employee2]

        name_to_employee, existing_codes = get_existing_employees(mock_db)

        assert "张三" in name_to_employee
        assert "李四" in name_to_employee
        assert "EMP-00001" in existing_codes
        assert "EMP-00002" in existing_codes


class TestGenerateEmployeeCode(unittest.TestCase):
    """测试 generate_employee_code 函数"""

    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_employee_code_empty(self):
        """测试空集合生成第一个工号"""
        existing_codes = set()
        code = generate_employee_code(existing_codes)
        assert code == "EMP-00001"
        assert code in existing_codes

    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_employee_code_with_existing(self):
        """测试已有工号的情况"""
        existing_codes = {"EMP-00001", "EMP-00002"}
        code = generate_employee_code(existing_codes)
        assert code == "EMP-00003"
        assert code in existing_codes

    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_employee_code_non_sequential(self):
        """测试非连续工号"""
        existing_codes = {"EMP-00001", "EMP-00005"}
        code = generate_employee_code(existing_codes)
        assert code == "EMP-00006"

    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_employee_code_conflict_resolution(self):
        """测试冲突解决"""
        existing_codes = {"EMP-00001"}
        # 模拟冲突场景（虽然实际很难发生）
        code = generate_employee_code(existing_codes)
        assert code not in {"EMP-00001"}


class TestBuildDepartmentName(unittest.TestCase):
    """测试 build_department_name 函数"""

    def test_build_department_name_all_levels(self):
        """测试三级部门都有值"""
        row = pd.Series({
            '一级部门': '技术中心',
            '二级部门': '研发部',
            '三级部门': '前端组'
        })
        assert build_department_name(row) == "技术中心-研发部-前端组"

    def test_build_department_name_partial(self):
        """测试部分部门有值"""
        row = pd.Series({
            '一级部门': '技术中心',
            '二级部门': '研发部',
            '三级部门': None
        })
        assert build_department_name(row) == "技术中心-研发部"

    def test_build_department_name_empty(self):
        """测试所有部门都为空"""
        row = pd.Series({
            '一级部门': None,
            '二级部门': None,
            '三级部门': None
        })
        assert build_department_name(row) is None

    def test_build_department_name_only_first(self):
        """测试只有一级部门"""
        row = pd.Series({'一级部门': '技术中心'})
        assert build_department_name(row) == "技术中心"


class TestDetermineEmploymentStatus(unittest.TestCase):
    """测试 determine_employment_status 函数"""

    def test_determine_employment_status_resigned(self):
        """测试离职状态"""
        row = pd.Series({'在职离职状态': '离职'})
        status, is_active = determine_employment_status(row)
        assert status == 'resigned'
        assert is_active is False

    def test_determine_employment_status_already_resigned(self):
        """测试已离职状态"""
        row = pd.Series({'在职离职状态': '已离职'})
        status, is_active = determine_employment_status(row)
        assert status == 'resigned'
        assert is_active is False

    def test_determine_employment_status_probation(self):
        """测试试用期状态"""
        row = pd.Series({'在职离职状态': '试用期'})
        status, is_active = determine_employment_status(row)
        assert status == 'active'
        assert is_active is True

    def test_determine_employment_status_active(self):
        """测试在职状态"""
        row = pd.Series({'在职离职状态': '在职'})
        status, is_active = determine_employment_status(row)
        assert status == 'active'
        assert is_active is True

    def test_determine_employment_status_empty(self):
        """测试空值默认为在职"""
        row = pd.Series({'在职离职状态': None})
        status, is_active = determine_employment_status(row)
        assert status == 'active'
        assert is_active is True


class TestDetermineEmploymentType(unittest.TestCase):
    """测试 determine_employment_type 函数"""

    def test_determine_employment_type_probation_not_confirmed(self):
        """测试未转正"""
        row = pd.Series({'是否转正': '否', '在职离职状态': '在职'})
        assert determine_employment_type(row) == 'probation'

    def test_determine_employment_type_probation_status(self):
        """测试试用期状态"""
        row = pd.Series({'是否转正': None, '在职离职状态': '试用期'})
        assert determine_employment_type(row) == 'probation'

    def test_determine_employment_type_regular(self):
        """测试正式员工"""
        row = pd.Series({'是否转正': '是', '在职离职状态': '在职'})
        assert determine_employment_type(row) == 'regular'

    def test_determine_employment_type_default(self):
        """测试默认为正式员工"""
        row = pd.Series({'是否转正': None, '在职离职状态': '在职'})
        assert determine_employment_type(row) == 'regular'


class TestCreateOrUpdateEmployee(unittest.TestCase):
    """测试 create_or_update_employee 函数"""

    @patch('app.services.hr_profile_import_service.generate_employee_code')
    @patch('app.services.hr_profile_import_service.build_department_name')
    @patch('app.services.hr_profile_import_service.determine_employment_status')
    @patch('app.services.hr_profile_import_service.determine_employment_type')
    def test_create_new_employee(self, mock_employment_type, mock_employment_status,
                                   mock_dept_name, mock_gen_code):
        """测试创建新员工"""
        mock_db = MagicMock()
        mock_gen_code.return_value = "EMP-00001"
        mock_dept_name.return_value = "技术部"
        mock_employment_status.return_value = ('active', True)
        mock_employment_type.return_value = 'regular'

        row = pd.Series({
            '姓名': '张三',
            '职务': '工程师',
            '联系方式': '13800138000',
            '身份证号': '110101199001011234'
        })

        name_to_employee = {}
        existing_codes = set()

        with patch('app.services.hr_profile_import_service.Employee') as MockEmployee:
            mock_employee_instance = MagicMock()
            MockEmployee.return_value = mock_employee_instance
            mock_employee_instance.id = 1

            employee, is_new = create_or_update_employee(
                mock_db, row, "张三", name_to_employee, existing_codes
            )

            assert is_new is True
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()

    def test_update_existing_employee(self):
        """测试更新现有员工"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.phone = "13800138000"
        mock_employee.id_card = "110101199001011234"

        row = pd.Series({
            '姓名': '张三',
            '联系方式': '13900139000',
            '身份证号': '110101199001015678'
        })

        name_to_employee = {"张三": mock_employee}
        existing_codes = {"EMP-00001"}

        employee, is_new = create_or_update_employee(
            mock_db, row, "张三", name_to_employee, existing_codes
        )

        assert is_new is False
        assert employee == mock_employee
        assert employee.phone == "13900139000"
        assert employee.id_card == "110101199001015678"

    def test_update_employee_partial_info(self):
        """测试部分更新员工信息"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.phone = "13800138000"
        mock_employee.id_card = "110101199001011234"

        row = pd.Series({
            '姓名': '张三',
            '联系方式': None,
            '身份证号': '110101199001015678'
        })

        name_to_employee = {"张三": mock_employee}
        existing_codes = {"EMP-00001"}

        employee, is_new = create_or_update_employee(
            mock_db, row, "张三", name_to_employee, existing_codes
        )

        assert is_new is False
        # phone 不应该被更新（因为 row 中是 None）
        assert employee.id_card == "110101199001015678"


class TestUpdateHrProfileFromRow(unittest.TestCase):
    """测试 update_hr_profile_from_row 函数"""

    def test_update_hr_profile_basic_info(self):
        """测试更新基本信息"""
        mock_db = MagicMock()
        mock_profile = MagicMock()

        row = pd.Series({
            '一级部门': '技术中心',
            '二级部门': '研发部',
            '三级部门': '前端组',
            '直接上级': '李经理',
            '职务': '高级工程师',
            '级别': 'P7',
            '性别': '男',
            '民族': '汉族',
            '政治面貌': '群众',
            '婚姻状况': '已婚'
        })

        update_hr_profile_from_row(mock_db, mock_profile, row)

        assert mock_profile.dept_level1 == '技术中心'
        assert mock_profile.dept_level2 == '研发部'
        assert mock_profile.dept_level3 == '前端组'
        assert mock_profile.direct_supervisor == '李经理'
        assert mock_profile.position == '高级工程师'
        assert mock_profile.job_level == 'P7'
        assert mock_profile.gender == '男'
        assert mock_profile.ethnicity == '汉族'
        assert mock_profile.political_status == '群众'
        assert mock_profile.marital_status == '已婚'

    def test_update_hr_profile_dates(self):
        """测试更新日期信息"""
        mock_db = MagicMock()
        mock_profile = MagicMock()

        row = pd.Series({
            '入职时间': '2024-01-15',
            '转正日期': '2024-04-15',
            '签订日期': '2024-01-10',
            '合同到期日': '2027-01-09',
            '出生年月': '1990-01-01',
            '离职日期': None
        })

        update_hr_profile_from_row(mock_db, mock_profile, row)

        assert mock_profile.hire_date is not None
        assert mock_profile.probation_end_date is not None
        assert mock_profile.contract_sign_date is not None
        assert mock_profile.contract_end_date is not None
        assert mock_profile.birth_date is not None

    def test_update_hr_profile_decimal_fields(self):
        """测试更新数值字段"""
        mock_db = MagicMock()
        mock_profile = MagicMock()

        row = pd.Series({
            '身高cm': 175,
            '体重kg': 70.5,
            '保险\n基数': 10000
        })

        update_hr_profile_from_row(mock_db, mock_profile, row)

        assert mock_profile.height_cm == Decimal('175')
        assert mock_profile.weight_kg == Decimal('70.5')
        assert mock_profile.insurance_base == Decimal('10000')

    def test_update_hr_profile_boolean_fields(self):
        """测试更新布尔字段"""
        mock_db = MagicMock()
        mock_profile = MagicMock()

        row = pd.Series({'是否转正': '是'})
        update_hr_profile_from_row(mock_db, mock_profile, row)
        assert mock_profile.is_confirmed is True

        row = pd.Series({'是否转正': '否'})
        update_hr_profile_from_row(mock_db, mock_profile, row)
        assert mock_profile.is_confirmed is False


class TestProcessHrProfileRow(unittest.TestCase):
    """测试 process_hr_profile_row 函数"""

    @patch('app.services.hr_profile_import_service.create_or_update_employee')
    @patch('app.services.hr_profile_import_service.update_hr_profile_from_row')
    def test_process_hr_profile_row_new_employee(self, mock_update_profile, mock_create_employee):
        """测试处理新员工"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.id = 1
        mock_create_employee.return_value = (mock_employee, True)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        row = pd.Series({'姓名': '张三'})
        name_to_employee = {}
        existing_codes = set()

        with patch('app.services.hr_profile_import_service.EmployeeHrProfile') as MockProfile:
            mock_profile_instance = MagicMock()
            MockProfile.return_value = mock_profile_instance

            result_code, error = process_hr_profile_row(
                mock_db, row, 0, name_to_employee, existing_codes
            )

            assert result_code == 1  # 新增
            assert error is None
            mock_db.add.assert_called()

    @patch('app.services.hr_profile_import_service.create_or_update_employee')
    @patch('app.services.hr_profile_import_service.update_hr_profile_from_row')
    def test_process_hr_profile_row_update_employee(self, mock_update_profile, mock_create_employee):
        """测试更新现有员工"""
        mock_db = MagicMock()
        mock_employee = MagicMock()
        mock_employee.id = 1
        mock_create_employee.return_value = (mock_employee, False)

        mock_profile = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile

        row = pd.Series({'姓名': '张三'})
        name_to_employee = {}
        existing_codes = set()

        result_code, error = process_hr_profile_row(
            mock_db, row, 0, name_to_employee, existing_codes
        )

        assert result_code == 2  # 更新
        assert error is None
        mock_update_profile.assert_called_once()

    def test_process_hr_profile_row_empty_name(self):
        """测试空姓名行"""
        mock_db = MagicMock()
        row = pd.Series({'姓名': None})
        name_to_employee = {}
        existing_codes = set()

        result_code, error = process_hr_profile_row(
            mock_db, row, 0, name_to_employee, existing_codes
        )

        assert result_code == 0  # 跳过
        assert error is None

    @patch('app.services.hr_profile_import_service.create_or_update_employee')
    def test_process_hr_profile_row_error(self, mock_create_employee):
        """测试处理异常情况"""
        mock_db = MagicMock()
        mock_create_employee.side_effect = Exception("Database error")

        row = pd.Series({'姓名': '张三'})
        name_to_employee = {}
        existing_codes = set()

        result_code, error = process_hr_profile_row(
            mock_db, row, 0, name_to_employee, existing_codes
        )

        assert result_code is None
        assert error is not None
        assert "第2行处理失败" in error


class TestImportHrProfilesFromDataframe(unittest.TestCase):
    """测试 import_hr_profiles_from_dataframe 函数"""

    @patch('app.services.hr_profile_import_service.get_existing_employees')
    @patch('app.services.hr_profile_import_service.process_hr_profile_row')
    def test_import_hr_profiles_success(self, mock_process_row, mock_get_existing):
        """测试成功导入"""
        mock_db = MagicMock()
        mock_get_existing.return_value = ({}, set())
        mock_process_row.side_effect = [(1, None), (2, None), (0, None)]

        df = pd.DataFrame({
            '姓名': ['张三', '李四', None]
        })

        result = import_hr_profiles_from_dataframe(mock_db, df)

        assert result['imported'] == 1
        assert result['updated'] == 1
        assert result['skipped'] == 1
        assert len(result['errors']) == 0

    @patch('app.services.hr_profile_import_service.get_existing_employees')
    @patch('app.services.hr_profile_import_service.process_hr_profile_row')
    def test_import_hr_profiles_with_errors(self, mock_process_row, mock_get_existing):
        """测试导入时有错误"""
        mock_db = MagicMock()
        mock_get_existing.return_value = ({}, set())
        mock_process_row.side_effect = [
            (1, None),
            (None, "第2行错误"),
            (None, "第3行错误")
        ]

        df = pd.DataFrame({
            '姓名': ['张三', '李四', '王五']
        })

        result = import_hr_profiles_from_dataframe(mock_db, df)

        assert result['imported'] == 1
        assert result['updated'] == 0
        assert result['skipped'] == 0
        assert len(result['errors']) == 2

    @patch('app.services.hr_profile_import_service.get_existing_employees')
    @patch('app.services.hr_profile_import_service.process_hr_profile_row')
    def test_import_hr_profiles_error_limit(self, mock_process_row, mock_get_existing):
        """测试错误信息限制在10条"""
        mock_db = MagicMock()
        mock_get_existing.return_value = ({}, set())

        # 生成15个错误
        errors = [(None, f"第{i}行错误") for i in range(15)]
        mock_process_row.side_effect = errors

        df = pd.DataFrame({
            '姓名': [f'员工{i}' for i in range(15)]
        })

        result = import_hr_profiles_from_dataframe(mock_db, df)

        assert len(result['errors']) == 10  # 最多返回10条错误

    @patch('app.services.hr_profile_import_service.get_existing_employees')
    @patch('app.services.hr_profile_import_service.process_hr_profile_row')
    def test_import_hr_profiles_empty_dataframe(self, mock_process_row, mock_get_existing):
        """测试空DataFrame"""
        mock_db = MagicMock()
        mock_get_existing.return_value = ({}, set())

        df = pd.DataFrame()

        result = import_hr_profiles_from_dataframe(mock_db, df)

        assert result['imported'] == 0
        assert result['updated'] == 0
        assert result['skipped'] == 0
        assert len(result['errors']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
