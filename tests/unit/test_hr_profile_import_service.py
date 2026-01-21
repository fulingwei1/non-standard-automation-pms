# -*- coding: utf-8 -*-
"""
Tests for hr_profile_import_service service
Covers: app/services/hr_profile_import_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 187 lines
Batch: 6
"""

import pytest
import pandas as pd
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

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
from app.models.organization import Employee, EmployeeHrProfile
from tests.conftest import _get_or_create_user


@pytest.fixture
def test_employee(db_session: Session):
    """创建测试员工"""
    employee = Employee(
        employee_code="EMP-00001",
        name="测试员工",
        department="技术部",
        role="工程师",
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


class TestCleanFunctions:
    """Test suite for clean functions."""

    def test_clean_str_valid(self):
        """测试清理字符串 - 有效值"""
        assert clean_str("测试字符串") == "测试字符串"
        assert clean_str("  带空格  ") == "带空格"

    def test_clean_str_nan(self):
        """测试清理字符串 - NaN值"""
        assert clean_str(pd.NA) is None
        assert clean_str(float('nan')) is None

    def test_clean_str_empty(self):
        """测试清理字符串 - 空值"""
        assert clean_str("") is None
        assert clean_str("/") is None
        assert clean_str("NaN") is None

    def test_clean_str_with_newline(self):
        """测试清理字符串 - 包含换行符"""
        assert clean_str("测试\n字符串") == "测试字符串"

    def test_clean_phone_valid(self):
        """测试清理电话号码 - 有效值"""
        assert clean_phone("13800138000") == "13800138000"
        assert clean_phone("  13800138000  ") == "13800138000"

    def test_clean_phone_scientific_notation(self):
        """测试清理电话号码 - 科学计数法"""
        assert clean_phone("1.38e+10") == "13800000000"
        assert clean_phone("13800138000.0") == "13800138000"

    def test_clean_phone_nan(self):
        """测试清理电话号码 - NaN值"""
        assert clean_phone(pd.NA) is None

    def test_parse_date_valid(self):
        """测试解析日期 - 有效值"""
        assert parse_date("2024-01-15") == datetime(2024, 1, 15).date()
        assert parse_date("2024/01/15") == datetime(2024, 1, 15).date()
        assert parse_date(datetime(2024, 1, 15)) == datetime(2024, 1, 15).date()

    def test_parse_date_invalid(self):
        """测试解析日期 - 无效值"""
        assert parse_date("invalid") is None
        assert parse_date(pd.NA) is None

    def test_clean_decimal_valid(self):
        """测试清理数值 - 有效值"""
        assert clean_decimal("100.50") == Decimal("100.50")
        assert clean_decimal(100.50) == Decimal("100.50")

    def test_clean_decimal_invalid(self):
        """测试清理数值 - 无效值"""
        assert clean_decimal("invalid") is None
        assert clean_decimal(pd.NA) is None


class TestValidationFunctions:
    """Test suite for validation functions."""

    def test_validate_excel_file_valid(self):
        """测试验证Excel文件 - 有效文件"""
        validate_excel_file("test.xlsx")
        validate_excel_file("test.xls")

    def test_validate_excel_file_invalid(self):
        """测试验证Excel文件 - 无效文件"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException, match="请上传Excel文件"):
            validate_excel_file("test.txt")

    def test_validate_required_columns_valid(self):
        """测试验证必需列 - 有效"""
        df = pd.DataFrame({"姓名": ["张三"], "工号": ["001"]})
        validate_required_columns(df)

    def test_validate_required_columns_missing(self):
        """测试验证必需列 - 缺少必需列"""
        from fastapi import HTTPException
        
        df = pd.DataFrame({"工号": ["001"]})
        
        with pytest.raises(HTTPException, match="必须包含'姓名'列"):
            validate_required_columns(df)


class TestEmployeeCodeGeneration:
    """Test suite for employee code generation."""

    def test_generate_employee_code_first(self):
        """测试生成员工工号 - 第一个"""
        existing_codes = set()
        code = generate_employee_code(existing_codes)
        
        assert code.startswith("EMP-")
        assert code in existing_codes

    def test_generate_employee_code_sequential(self):
        """测试生成员工工号 - 连续生成"""
        existing_codes = {"EMP-00001", "EMP-00002"}
        code = generate_employee_code(existing_codes)
        
        assert code == "EMP-00003"
        assert code in existing_codes

    def test_generate_employee_code_skip_conflict(self):
        """测试生成员工工号 - 跳过冲突"""
        existing_codes = {"EMP-00001", "EMP-00002", "EMP-00003"}
        code = generate_employee_code(existing_codes)
        
        assert code == "EMP-00004"
        assert code in existing_codes


class TestDepartmentNameBuilding:
    """Test suite for department name building."""

    def test_build_department_name_single(self):
        """测试组合部门名称 - 单级部门"""
        row = pd.Series({"一级部门": "技术部"})
        result = build_department_name(row)
        
        assert result == "技术部"

    def test_build_department_name_multi(self):
        """测试组合部门名称 - 多级部门"""
        row = pd.Series({
            "一级部门": "技术部",
            "二级部门": "研发组",
            "三级部门": "前端组"
        })
        result = build_department_name(row)
        
        assert result == "技术部-研发组-前端组"

    def test_build_department_name_empty(self):
        """测试组合部门名称 - 空值"""
        row = pd.Series({})
        result = build_department_name(row)
        
        assert result is None


class TestEmploymentStatus:
    """Test suite for employment status determination."""

    def test_determine_employment_status_resigned(self):
        """测试确定在职状态 - 离职"""
        row = pd.Series({"在职离职状态": "离职"})
        status, is_active = determine_employment_status(row)
        
        assert status == "resigned"
        assert is_active is False

    def test_determine_employment_status_probation(self):
        """测试确定在职状态 - 试用期"""
        row = pd.Series({"在职离职状态": "试用期"})
        status, is_active = determine_employment_status(row)
        
        assert status == "active"
        assert is_active is True

    def test_determine_employment_status_active(self):
        """测试确定在职状态 - 在职"""
        row = pd.Series({"在职离职状态": "在职"})
        status, is_active = determine_employment_status(row)
        
        assert status == "active"
        assert is_active is True

    def test_determine_employment_type_probation(self):
        """测试确定员工类型 - 试用期"""
        row = pd.Series({
            "是否转正": "否",
            "在职离职状态": "试用期"
        })
        result = determine_employment_type(row)
        
        assert result == "probation"

    def test_determine_employment_type_regular(self):
        """测试确定员工类型 - 正式员工"""
        row = pd.Series({
            "是否转正": "是",
            "在职离职状态": "在职"
        })
        result = determine_employment_type(row)
        
        assert result == "regular"


class TestEmployeeOperations:
    """Test suite for employee operations."""

    def test_get_existing_employees_empty(self, db_session):
        """测试获取现有员工 - 空数据库"""
        name_map, codes = get_existing_employees(db_session)
        
        assert isinstance(name_map, dict)
        assert isinstance(codes, set)

    def test_get_existing_employees_with_data(self, db_session, test_employee):
        """测试获取现有员工 - 有数据"""
        name_map, codes = get_existing_employees(db_session)
        
        assert "测试员工" in name_map
        assert "EMP-00001" in codes

    def test_create_or_update_employee_new(self, db_session):
        """测试创建或更新员工 - 新员工"""
        row = pd.Series({
            "姓名": "新员工",
            "工号": None,
            "部门": "技术部",
            "职务": "工程师"
        })
        name_map = {}
        existing_codes = set()
        
        employee, is_new = create_or_update_employee(
            db_session,
            row,
            "新员工",
            name_map,
            existing_codes
        )
        
        assert employee is not None
        assert is_new is True
        assert employee.name == "新员工"
        assert employee.employee_code is not None

    def test_create_or_update_employee_existing(self, db_session, test_employee):
        """测试创建或更新员工 - 已存在员工"""
        row = pd.Series({
            "姓名": "测试员工",
            "工号": "EMP-00001",
            "部门": "技术部",
            "职务": "高级工程师",
            "联系方式": "13800138000"
        })
        name_map = {"测试员工": test_employee}
        existing_codes = {"EMP-00001"}
        
        employee, is_new = create_or_update_employee(
            db_session,
            row,
            "测试员工",
            name_map,
            existing_codes
        )
        
        assert employee.id == test_employee.id
        assert is_new is False
        assert employee.phone == "13800138000"

    def test_update_hr_profile_from_row(self, db_session, test_employee):
        """测试更新人事档案"""
        profile = EmployeeHrProfile(employee_id=test_employee.id)
        db_session.add(profile)
        db_session.commit()
        
        row = pd.Series({
            "一级部门": "技术部",
            "二级部门": "研发组",
            "职务": "高级工程师",
            "入职时间": "2024-01-01",
            "性别": "男",
            "年龄": 30
        })
        
        update_hr_profile_from_row(db_session, profile, row)
        db_session.commit()
        db_session.refresh(profile)
        
        assert profile.dept_level1 == "技术部"
        assert profile.dept_level2 == "研发组"
        assert profile.position == "高级工程师"
        assert profile.gender == "男"
        assert profile.age == 30

    def test_process_hr_profile_row_new(self, db_session):
        """测试处理HR档案行 - 新员工"""
        row = pd.Series({
            "姓名": "新员工",
            "部门": "技术部",
            "职务": "工程师"
        })
        name_map = {}
        existing_codes = set()
        
        result_code, error = process_hr_profile_row(
            db_session,
            row,
            0,
            name_map,
            existing_codes
        )
        
        assert result_code == 1  # 新增
        assert error is None

    def test_process_hr_profile_row_update(self, db_session, test_employee):
        """测试处理HR档案行 - 更新员工"""
        # 创建人事档案
        profile = EmployeeHrProfile(employee_id=test_employee.id)
        db_session.add(profile)
        db_session.commit()
        
        row = pd.Series({
            "姓名": "测试员工",
            "部门": "技术部",
            "职务": "高级工程师"
        })
        name_map = {"测试员工": test_employee}
        existing_codes = {"EMP-00001"}
        
        result_code, error = process_hr_profile_row(
            db_session,
            row,
            0,
            name_map,
            existing_codes
        )
        
        assert result_code == 2  # 更新
        assert error is None

    def test_process_hr_profile_row_skip(self, db_session):
        """测试处理HR档案行 - 跳过（无姓名）"""
        row = pd.Series({
            "姓名": None,
            "部门": "技术部"
        })
        name_map = {}
        existing_codes = set()
        
        result_code, error = process_hr_profile_row(
            db_session,
            row,
            0,
            name_map,
            existing_codes
        )
        
        assert result_code == 0  # 跳过
        assert error is None

    def test_import_hr_profiles_from_dataframe_success(self, db_session):
        """测试从DataFrame导入HR档案 - 成功场景"""
        df = pd.DataFrame({
            "姓名": ["员工1", "员工2"],
            "部门": ["技术部", "销售部"],
            "职务": ["工程师", "销售"]
        })
        
        result = import_hr_profiles_from_dataframe(db_session, df)
        
        assert result["imported"] == 2
        assert result["updated"] == 0
        assert result["skipped"] == 0
        assert len(result["errors"]) == 0

    def test_import_hr_profiles_from_dataframe_with_errors(self, db_session):
        """测试从DataFrame导入HR档案 - 包含错误"""
        df = pd.DataFrame({
            "姓名": ["员工1", None, "员工3"],
            "部门": ["技术部", "销售部", "技术部"],
            "职务": ["工程师", "销售", "工程师"]
        })
        
        result = import_hr_profiles_from_dataframe(db_session, df)
        
        assert result["imported"] >= 1
        assert result["skipped"] >= 1
        assert isinstance(result["errors"], list)
