# -*- coding: utf-8 -*-
"""HR档案导入服务测试"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.hr_profile_import_service import (
    clean_str, clean_phone, parse_date, clean_decimal,
    validate_excel_file, validate_required_columns,
    get_existing_employees, generate_employee_code,
    build_department_name, determine_employment_status,
    determine_employment_type, import_hr_profiles_from_dataframe,
)


class TestCleanStr:
    def test_normal(self):
        assert clean_str("hello") == "hello"

    def test_nan(self):
        import numpy as np
        assert clean_str(np.nan) is None

    def test_slash(self):
        assert clean_str("/") is None

    def test_newline(self):
        assert clean_str("hello\nworld") == "helloworld"

    def test_empty(self):
        assert clean_str("") is None


class TestCleanPhone:
    def test_normal(self):
        assert clean_phone("13800138000") == "13800138000"

    def test_scientific_notation(self):
        result = clean_phone("1.38e10")
        assert result == "13800000000"

    def test_nan(self):
        import numpy as np
        assert clean_phone(np.nan) is None


class TestParseDate:
    def test_datetime(self):
        dt = datetime(2026, 1, 15)
        result = parse_date(dt)
        assert result.year == 2026

    def test_string_dash(self):
        result = parse_date("2026-01-15")
        assert result is not None

    def test_string_slash(self):
        result = parse_date("2026/01/15")
        assert result is not None

    def test_invalid(self):
        result = parse_date("not-a-date")
        assert result is None

    def test_nan(self):
        import numpy as np
        assert parse_date(np.nan) is None


class TestCleanDecimal:
    def test_normal(self):
        assert clean_decimal("100.50") == Decimal("100.50")

    def test_nan(self):
        import numpy as np
        assert clean_decimal(np.nan) is None

    def test_invalid(self):
        assert clean_decimal("abc") is None


class TestValidateExcelFile:
    def test_valid_xlsx(self):
        validate_excel_file("test.xlsx")  # should not raise

    def test_invalid_file(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("test.csv")


class TestValidateRequiredColumns:
    def test_missing_name_column(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"其他": [1]})
        with pytest.raises(HTTPException):
            validate_required_columns(df)

    def test_valid(self):
        df = pd.DataFrame({"姓名": ["张三"]})
        validate_required_columns(df)


class TestBuildDepartmentName:
    def test_full_dept(self):
        row = pd.Series({"一级部门": "技术中心", "二级部门": "软件部", "三级部门": "前端组"})
        assert build_department_name(row) == "技术中心-软件部-前端组"

    def test_partial_dept(self):
        row = pd.Series({"一级部门": "技术中心"})
        assert build_department_name(row) == "技术中心"

    def test_no_dept(self):
        row = pd.Series({})
        assert build_department_name(row) is None


class TestDetermineEmploymentStatus:
    def test_active(self):
        row = pd.Series({"在职离职状态": "在职"})
        status, active = determine_employment_status(row)
        assert status == "active"
        assert active is True

    def test_resigned(self):
        row = pd.Series({"在职离职状态": "离职"})
        status, active = determine_employment_status(row)
        assert status == "resigned"
        assert active is False

    def test_probation(self):
        row = pd.Series({"在职离职状态": "试用期"})
        status, active = determine_employment_status(row)
        assert status == "active"
        assert active is True


class TestDetermineEmploymentType:
    def test_probation(self):
        row = pd.Series({"是否转正": "否"})
        assert determine_employment_type(row) == "probation"

    def test_regular(self):
        row = pd.Series({"是否转正": "是"})
        assert determine_employment_type(row) == "regular"


class TestGenerateEmployeeCode:
    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_new_code(self):
        existing = set()
        code = generate_employee_code(existing)
        assert code.startswith("EMP-")
        assert code in existing  # should be added

    @patch('app.utils.code_config.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.utils.code_config.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate_code_with_existing(self):
        existing = {"EMP-00001"}
        code = generate_employee_code(existing)
        assert code == "EMP-00002"


class TestImportHrProfiles:
    def test_import_empty_dataframe(self):
        db = MagicMock()
        db.query.return_value.all.return_value = []
        df = pd.DataFrame({"姓名": []})
        result = import_hr_profiles_from_dataframe(db, df)
        assert result["imported"] == 0
        assert result["updated"] == 0
