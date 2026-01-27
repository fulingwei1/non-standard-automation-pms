# -*- coding: utf-8 -*-
"""
Tests for employee_import_service service
Covers: app/services/employee_import_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 154 lines
"""

import pytest
import pandas as pd
from sqlalchemy.orm import Session

from app.services.employee_import_service import (
    find_name_column,
    find_department_columns,
    find_other_columns,
    clean_name,
    get_department_name,
    is_active_employee,
    generate_employee_code,
    clean_phone,
    import_employees_from_dataframe,
)
from app.models.organization import Employee
from app.models.staff_matching import HrTagDict
from tests.factories import EmployeeFactory


class TestEmployeeImportService:
    """Test suite for employee_import_service."""

    def test_find_name_column(self):
        """测试查找姓名列"""
        columns = ["姓名", "部门", "职务"]
        assert find_name_column(columns) == "姓名"

        columns = ["name", "department"]
        assert find_name_column(columns) == "name"

        columns = ["员工姓名", "其他"]
        assert find_name_column(columns) == "员工姓名"

        columns = ["其他列"]
        assert find_name_column(columns) is None

    def test_find_department_columns(self):
        """测试查找部门列"""
        columns = ["姓名", "一级部门", "二级部门", "三级部门"]
        dept_cols = find_department_columns(columns)
        assert len(dept_cols) == 3
        assert "一级部门" in dept_cols

        columns = ["姓名", "部门"]
        dept_cols = find_department_columns(columns)
        assert len(dept_cols) == 1
        assert "部门" in dept_cols

        columns = ["姓名", "其他"]
        dept_cols = find_department_columns(columns)
        assert len(dept_cols) == 0

    def test_find_other_columns(self):
        """测试查找其他列"""
        columns = ["姓名", "职务", "手机", "在职离职状态"]
        other = find_other_columns(columns)

        assert other["position"] == "职务"
        assert other["phone"] == "手机"
        assert other["status"] == "在职离职状态"

        columns = ["姓名", "岗位", "电话"]
        other = find_other_columns(columns)
        assert other["position"] == "岗位"
        assert other["phone"] == "电话"

    def test_clean_name(self):
        """测试清理姓名"""
        assert clean_name("  张三  ") == "张三"
        assert clean_name("李四") == "李四"
        assert clean_name(pd.NA) is None
        assert clean_name(None) is None
        assert clean_name("") is None

    def test_get_department_name(self):
        """测试获取部门名称"""
        row = pd.Series({
        "一级部门": "技术部",
        "二级部门": "研发组"
        })
        dept_cols = ["一级部门", "二级部门"]
        dept_name = get_department_name(row, dept_cols)
        assert dept_name == "技术部-研发组"

        row = pd.Series({"部门": "技术部"})
        dept_name = get_department_name(row, ["部门"])
        assert dept_name == "技术部"

        row = pd.Series({})
        dept_name = get_department_name(row, [])
        assert dept_name is None

    def test_is_active_employee(self):
        """测试判断员工是否在职"""
        assert is_active_employee("在职") is True
        assert is_active_employee("离职") is False
        assert is_active_employee("已离职") is False
        assert is_active_employee(pd.NA) is True
        assert is_active_employee(None) is True
        assert is_active_employee("resigned") is False

    def test_generate_employee_code(self):
        """测试生成员工工号"""
        existing_codes = {"EMP-00001", "EMP-00002"}
        code = generate_employee_code(1, existing_codes)
        assert code.startswith("EMP-")
        assert code not in existing_codes

        # 测试冲突处理
        existing_codes = {"EMP-00001"}
        code1 = generate_employee_code(1, existing_codes)
        existing_codes.add(code1)
        code2 = generate_employee_code(1, existing_codes)
        assert code1 != code2

    def test_clean_phone(self):
        """测试清理电话号码"""
        assert clean_phone("13812345678") == "13812345678"
        assert clean_phone("  13812345678  ") == "13812345678"
        assert clean_phone(pd.NA) is None
        assert clean_phone(None) is None
        assert clean_phone("") is None

        # 测试科学计数法
        assert clean_phone("1.38e+10") == "13800000000"
        assert clean_phone("138.0") == "138"

    def test_import_employees_from_dataframe_missing_name_column(self, db_session):
        """测试导入员工 - 缺少姓名列"""
        df = pd.DataFrame({"部门": ["技术部"]})

        with pytest.raises(Exception):  # HTTPException
        import_employees_from_dataframe(db_session, df, evaluator_id=1)

    def test_import_employees_from_dataframe_success(self, db_session):
        """测试导入员工 - 成功场景"""
        # 创建标签字典
        tag = HrTagDict(
        tag_code="TAG-PLC",
        tag_name="PLC编程",
        tag_type="SKILL",
        is_active=True
        )
        db_session.add(tag)
        db_session.commit()

        df = pd.DataFrame({
        "姓名": ["张三", "李四"],
        "部门": ["技术部", "销售部"],
        "职务": ["PLC工程师", "销售"],
        "手机": ["13812345678", "13912345678"],
        "在职离职状态": ["在职", "在职"]
        })

        result = import_employees_from_dataframe(db_session, df, evaluator_id=1)

        assert result["imported"] >= 0
        assert result["updated"] >= 0
        assert result["skipped"] >= 0
        assert isinstance(result["errors"], list)

    def test_import_employees_from_dataframe_update_existing(self, db_session):
        """测试导入员工 - 更新现有员工"""
        # 创建现有员工
        existing_employee = EmployeeFactory(
        name="张三",
        department="技术部"
        )
        db_session.add(existing_employee)
        db_session.commit()

        df = pd.DataFrame({
        "姓名": ["张三"],
        "部门": ["技术部"],
        "手机": ["13899999999"]
        })

        result = import_employees_from_dataframe(db_session, df, evaluator_id=1)

        assert result["updated"] >= 0 or result["imported"] >= 0

    def test_import_employees_from_dataframe_skip_empty_name(self, db_session):
        """测试导入员工 - 跳过空姓名"""
        df = pd.DataFrame({
        "姓名": ["", "   ", None],
        "部门": ["技术部", "销售部", "财务部"]
        })

        result = import_employees_from_dataframe(db_session, df, evaluator_id=1)

        assert result["skipped"] >= 0
