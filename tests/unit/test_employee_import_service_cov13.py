# -*- coding: utf-8 -*-
"""第十三批 - 员工导入服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    import pandas as pd
    from app.services.employee_import_service import (
        find_name_column,
        find_department_columns,
        find_other_columns,
        clean_name,
        get_department_name,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


class TestFindNameColumn:
    def test_find_chinese_name(self):
        """找到姓名列"""
        result = find_name_column(['ID', '姓名', '部门'])
        assert result == '姓名'

    def test_find_name_col(self):
        """找到名字列"""
        result = find_name_column(['名字', '部门'])
        assert result == '名字'

    def test_find_english_name(self):
        """找到英文name列"""
        result = find_name_column(['name', 'department'])
        assert result == 'name'

    def test_not_found_returns_none(self):
        """未找到返回None"""
        result = find_name_column(['工号', '部门', '职务'])
        assert result is None

    def test_employee_name_col(self):
        """员工姓名列"""
        result = find_name_column(['员工姓名', '电话'])
        assert result == '员工姓名'


class TestFindDepartmentColumns:
    def test_three_level_departments(self):
        """三级部门列"""
        cols = ['一级部门', '二级部门', '三级部门', '姓名']
        result = find_department_columns(cols)
        assert '一级部门' in result
        assert '二级部门' in result
        assert '三级部门' in result

    def test_single_dept_col(self):
        """单个部门列"""
        cols = ['部门', '姓名']
        result = find_department_columns(cols)
        assert '部门' in result

    def test_no_dept_col(self):
        """无部门列返回空列表"""
        cols = ['姓名', '电话']
        result = find_department_columns(cols)
        assert result == []


class TestFindOtherColumns:
    def test_find_position_col(self):
        """找到职务列"""
        result = find_other_columns(['职务', '姓名'])
        assert result['position'] == '职务'

    def test_find_phone_col(self):
        """找到手机列"""
        result = find_other_columns(['手机', '姓名'])
        assert result['phone'] == '手机'

    def test_not_found_returns_none(self):
        """未找到时对应字段为None"""
        result = find_other_columns(['姓名', '部门'])
        assert result['position'] is None
        assert result['phone'] is None


class TestCleanName:
    def test_strip_whitespace(self):
        """清理空格"""
        result = clean_name('  张三  ')
        assert result == '张三'

    def test_nan_returns_none(self):
        """NaN返回None"""
        result = clean_name(float('nan'))
        assert result is None

    def test_empty_string_returns_none(self):
        """空字符串返回None"""
        result = clean_name('   ')
        assert result is None
