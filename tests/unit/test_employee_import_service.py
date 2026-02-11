# -*- coding: utf-8 -*-
"""员工导入服务测试"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.employee_import_service import (
    find_name_column, find_department_columns, find_other_columns,
    clean_name, get_department_name, is_active_employee,
    generate_employee_code, clean_phone, import_employees_from_dataframe,
)


class TestFindNameColumn:
    def test_found(self):
        assert find_name_column(['姓名', '部门']) == '姓名'

    def test_english(self):
        assert find_name_column(['name', 'dept']) == 'name'

    def test_not_found(self):
        assert find_name_column(['部门', '电话']) is None


class TestFindDepartmentColumns:
    def test_multi_level(self):
        cols = find_department_columns(['一级部门', '二级部门', '三级部门'])
        assert len(cols) == 3

    def test_single(self):
        cols = find_department_columns(['部门'])
        assert cols == ['部门']

    def test_none(self):
        assert find_department_columns(['姓名']) == []


class TestFindOtherColumns:
    def test_found(self):
        result = find_other_columns(['职务', '联系方式', '在职离职状态'])
        assert result['position'] == '职务'
        assert result['phone'] == '联系方式'
        assert result['status'] == '在职离职状态'

    def test_not_found(self):
        result = find_other_columns(['姓名'])
        assert result['position'] is None


class TestCleanName:
    def test_normal(self):
        assert clean_name("张三") == "张三"

    def test_nan(self):
        import numpy as np
        assert clean_name(np.nan) is None

    def test_empty(self):
        assert clean_name("") is None


class TestGetDepartmentName:
    def test_multi_level(self):
        row = pd.Series({"一级部门": "技术", "二级部门": "软件"})
        assert get_department_name(row, ["一级部门", "二级部门"]) == "技术-软件"

    def test_no_cols(self):
        assert get_department_name(pd.Series(), []) is None


class TestIsActiveEmployee:
    def test_active(self):
        assert is_active_employee("在职") is True

    def test_resigned(self):
        assert is_active_employee("离职") is False

    def test_nan(self):
        import numpy as np
        assert is_active_employee(np.nan) is True


class TestCleanPhone:
    def test_normal(self):
        assert clean_phone("13800138000") == "13800138000"

    def test_scientific(self):
        assert clean_phone("1.38e10") == "13800000000"

    def test_nan(self):
        import numpy as np
        assert clean_phone(np.nan) is None


class TestGenerateEmployeeCode:
    @patch('app.services.employee_import_service.CODE_PREFIX', {'EMPLOYEE': 'EMP'})
    @patch('app.services.employee_import_service.SEQ_LENGTH', {'EMPLOYEE': 5})
    def test_generate(self):
        existing = set()
        code = generate_employee_code(1, existing)
        assert code.startswith("EMP-")


class TestImportEmployees:
    def test_missing_name_column(self):
        from fastapi import HTTPException
        db = MagicMock()
        df = pd.DataFrame({"部门": ["技术"]})
        with pytest.raises(HTTPException):
            import_employees_from_dataframe(db, df, evaluator_id=1)

    def test_empty_dataframe(self):
        db = MagicMock()
        db.query.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        df = pd.DataFrame({"姓名": []})
        result = import_employees_from_dataframe(db, df, evaluator_id=1)
        assert result["imported"] == 0
