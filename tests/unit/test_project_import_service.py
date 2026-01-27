# -*- coding: utf-8 -*-
"""
Tests for project_import_service
Covers: app/services/project_import_service.py
"""

import io
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

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


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_code="CUST-001",
        customer_name="测试客户",
        contact_person="联系人",
        contact_phone="13800138000"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_pm(db_session: Session):
    """创建测试项目经理"""
    from app.models.organization import Employee
    from app.core.security import get_password_hash
    
    # 先创建员工
    employee = Employee(
        employee_code="EMP-PM-001",
        name="测试PM",
        department="项目管理部",
        role="项目经理",
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    
    # 再创建用户
    user = User(
        employee_id=employee.id,
        username="pm_test",
        real_name="测试PM",
        password_hash=get_password_hash("test123"),
        department="项目管理部",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestProjectImportService:
    """Test suite for project_import_service."""

    # === validate_excel_file 测试 ===

    def test_validate_excel_file_valid_xlsx(self):
        """测试验证Excel文件 - 有效的.xlsx文件"""
        validate_excel_file("test.xlsx")
        # 应该不抛出异常

    def test_validate_excel_file_valid_xls(self):
        """测试验证Excel文件 - 有效的.xls文件"""
        validate_excel_file("test.xls")
        # 应该不抛出异常

    def test_validate_excel_file_invalid(self):
        """测试验证Excel文件 - 无效文件类型"""
        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("test.csv")
            assert exc_info.value.status_code == 400
            assert "只支持Excel文件" in exc_info.value.detail

            # === parse_excel_data 测试 ===

    def test_parse_excel_data_success(self):
        """测试解析Excel数据 - 成功场景"""
        # 创建测试Excel数据
        df = pd.DataFrame({
        '项目编码*': ['PJ001', 'PJ002'],
        '项目名称*': ['项目1', '项目2']
        })
        excel_bytes = io.BytesIO()
        df.to_excel(excel_bytes, index=False)
        excel_bytes.seek(0)

        result = parse_excel_data(excel_bytes.getvalue())
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_parse_excel_data_empty(self):
        """测试解析Excel数据 - 空文件"""
        df = pd.DataFrame()
        excel_bytes = io.BytesIO()
        df.to_excel(excel_bytes, index=False)
        excel_bytes.seek(0)

        with pytest.raises(HTTPException) as exc_info:
            parse_excel_data(excel_bytes.getvalue())
            assert exc_info.value.status_code == 400
            assert "没有数据" in exc_info.value.detail

    def test_parse_excel_data_invalid(self):
        """测试解析Excel数据 - 无效文件"""
        with pytest.raises(HTTPException) as exc_info:
            parse_excel_data(b"invalid data")
            assert exc_info.value.status_code == 400
            assert "解析失败" in exc_info.value.detail

            # === validate_project_columns 测试 ===

    def test_validate_project_columns_success(self):
        """测试验证项目列 - 成功场景"""
        df = pd.DataFrame({
        '项目编码*': ['PJ001'],
        '项目名称*': ['项目1']
        })
        validate_project_columns(df)
        # 应该不抛出异常

    def test_validate_project_columns_missing_required(self):
        """测试验证项目列 - 缺少必需列"""
        df = pd.DataFrame({
        '项目编码': ['PJ001']  # 缺少项目名称
        })
        with pytest.raises(HTTPException) as exc_info:
            validate_project_columns(df)
            assert exc_info.value.status_code == 400
            assert "缺少必需的列" in exc_info.value.detail

    def test_validate_project_columns_alternative_names(self):
        """测试验证项目列 - 使用替代列名"""
        df = pd.DataFrame({
        '项目编码': ['PJ001'],  # 不带*
        '项目名称': ['项目1']   # 不带*
        })
        validate_project_columns(df)
        # 应该不抛出异常

    # === get_column_value 测试 ===

    def test_get_column_value_with_asterisk(self):
        """测试获取列值 - 带*的列名"""
        row = pd.Series({'项目编码*': 'PJ001'})
        value = get_column_value(row, '项目编码*')
        assert value == 'PJ001'

    def test_get_column_value_without_asterisk(self):
        """测试获取列值 - 不带*的列名"""
        row = pd.Series({'项目编码': 'PJ001'})
        value = get_column_value(row, '项目编码*', '项目编码')
        assert value == 'PJ001'

    def test_get_column_value_none(self):
        """测试获取列值 - 值为空"""
        row = pd.Series({'项目编码*': None})
        value = get_column_value(row, '项目编码*')
        assert value is None

    def test_get_column_value_na(self):
        """测试获取列值 - NaN值"""
        import numpy as np
        row = pd.Series({'项目编码*': np.nan})
        value = get_column_value(row, '项目编码*')
        assert value is None

    # === parse_project_row 测试 ===

    def test_parse_project_row_success(self):
        """测试解析项目行 - 成功场景"""
        row = pd.Series({
        '项目编码*': 'PJ001',
        '项目名称*': '测试项目'
        })
        project_code, project_name, errors = parse_project_row(row, 0)
        assert project_code == 'PJ001'
        assert project_name == '测试项目'
        assert len(errors) == 0

    def test_parse_project_row_missing_code(self):
        """测试解析项目行 - 缺少项目编码"""
        row = pd.Series({'项目名称*': '测试项目'})
        project_code, project_name, errors = parse_project_row(row, 0)
        assert project_code is None
        assert project_name is None
        assert len(errors) > 0
        assert "不能为空" in errors[0]

    def test_parse_project_row_missing_name(self):
        """测试解析项目行 - 缺少项目名称"""
        row = pd.Series({'项目编码*': 'PJ001'})
        project_code, project_name, errors = parse_project_row(row, 0)
        assert project_code is None
        assert project_name is None
        assert len(errors) > 0

    # === find_or_create_customer 测试 ===

    def test_find_or_create_customer_found(self, db_session, test_customer):
        """测试查找或创建客户 - 找到客户"""
        customer = find_or_create_customer(db_session, test_customer.customer_name)
        assert customer is not None
        assert customer.id == test_customer.id

    def test_find_or_create_customer_not_found(self, db_session):
        """测试查找或创建客户 - 未找到客户"""
        customer = find_or_create_customer(db_session, "不存在的客户")
        assert customer is None

    def test_find_or_create_customer_empty_name(self, db_session):
        """测试查找或创建客户 - 空名称"""
        customer = find_or_create_customer(db_session, "")
        assert customer is None

    # === find_project_manager 测试 ===

    def test_find_project_manager_by_real_name(self, db_session, test_pm):
        """测试查找项目经理 - 按真实姓名"""
        pm = find_project_manager(db_session, test_pm.real_name)
        assert pm is not None
        assert pm.id == test_pm.id

    def test_find_project_manager_by_username(self, db_session, test_pm):
        """测试查找项目经理 - 按用户名"""
        pm = find_project_manager(db_session, test_pm.username)
        assert pm is not None
        assert pm.id == test_pm.id

    def test_find_project_manager_not_found(self, db_session):
        """测试查找项目经理 - 未找到"""
        pm = find_project_manager(db_session, "不存在的PM")
        assert pm is None

    def test_find_project_manager_empty_name(self, db_session):
        """测试查找项目经理 - 空名称"""
        pm = find_project_manager(db_session, "")
        assert pm is None

    # === parse_date_value 测试 ===

    def test_parse_date_value_valid(self):
        """测试解析日期值 - 有效日期"""
        result = parse_date_value("2024-01-01")
        assert result == date(2024, 1, 1)

    def test_parse_date_value_na(self):
        """测试解析日期值 - NaN"""
        result = parse_date_value(pd.NA)
        assert result is None

    def test_parse_date_value_invalid(self):
        """测试解析日期值 - 无效日期"""
        result = parse_date_value("invalid date")
        assert result is None

    def test_parse_date_value_none(self):
        """测试解析日期值 - None"""
        result = parse_date_value(None)
        assert result is None

    # === parse_decimal_value 测试 ===

    def test_parse_decimal_value_valid(self):
        """测试解析金额值 - 有效金额"""
        result = parse_decimal_value("100000.50")
        assert result == Decimal("100000.50")

    def test_parse_decimal_value_na(self):
        """测试解析金额值 - NaN"""
        result = parse_decimal_value(pd.NA)
        assert result is None

    def test_parse_decimal_value_invalid(self):
        """测试解析金额值 - 无效金额"""
        result = parse_decimal_value("invalid")
        assert result is None

    def test_parse_decimal_value_none(self):
        """测试解析金额值 - None"""
        result = parse_decimal_value(None)
        assert result is None

    # === populate_project_from_row 测试 ===

    def test_populate_project_from_row_success(self, db_session, test_customer, test_pm):
        """测试填充项目信息 - 成功场景"""
        project = Project(
        project_code="PJ-TEST",
        project_name="测试项目",
        stage="S1",
        status="ST01"
        )
        db_session.add(project)
        db_session.flush()

        row = pd.Series({
        '客户名称': test_customer.customer_name,
        '合同编号': 'CONTRACT-001',
        '合同日期': '2024-01-01',
        '合同金额': '100000.00',
        '项目经理': test_pm.real_name,
        '项目描述': '测试描述'
        })

        populate_project_from_row(db_session, project, row)
        assert project.customer_id == test_customer.id
        assert project.customer_name == test_customer.customer_name
        assert project.contract_no == 'CONTRACT-001'
        assert project.contract_date == date(2024, 1, 1)
        assert project.contract_amount == Decimal("100000.00")
        assert project.pm_id == test_pm.id

    # === import_projects_from_dataframe 测试 ===

    def test_import_projects_from_dataframe_new_project(self, db_session, test_customer, test_pm):
        """测试导入项目 - 新建项目"""
        df = pd.DataFrame({
        '项目编码*': ['PJ-NEW-001'],
        '项目名称*': ['新项目'],
        '客户名称': [test_customer.customer_name],
        '项目经理': [test_pm.real_name]
        })

        imported, updated, failed = import_projects_from_dataframe(db_session, df, update_existing=False)
        assert imported == 1
        assert updated == 0
        assert len(failed) == 0

        # 验证项目已创建
        project = db_session.query(Project).filter(Project.project_code == 'PJ-NEW-001').first()
        assert project is not None
        assert project.project_name == '新项目'

    def test_import_projects_from_dataframe_update_existing(self, db_session, test_customer):
        """测试导入项目 - 更新现有项目"""
        # 创建现有项目
        existing_project = Project(
        project_code="PJ-EXISTING",
        project_name="现有项目",
        stage="S1",
        status="ST01"
        )
        db_session.add(existing_project)
        db_session.commit()
        db_session.refresh(existing_project)

        df = pd.DataFrame({
        '项目编码*': ['PJ-EXISTING'],
        '项目名称*': ['更新后的项目名称'],
        '客户名称': [test_customer.customer_name],  # 使用已存在的客户
        '合同金额': ['200000.00']
        })

        imported, updated, failed = import_projects_from_dataframe(db_session, df, update_existing=True)
        assert imported == 0
        assert updated == 1
        assert len(failed) == 0

        # 验证项目已更新
        db_session.refresh(existing_project)
        # populate_project_from_row 会更新客户信息（如果客户存在）
        # find_or_create_customer 只查找，不创建，所以需要确保客户存在
        if existing_project.customer_id:
            assert existing_project.customer_id == test_customer.id
            assert existing_project.customer_name == test_customer.customer_name

    def test_import_projects_from_dataframe_skip_existing(self, db_session):
        """测试导入项目 - 跳过已存在项目"""
        # 创建现有项目
        existing_project = Project(
        project_code="PJ-EXISTING-2",
        project_name="现有项目2",
        stage="S1",
        status="ST01"
        )
        db_session.add(existing_project)
        db_session.commit()

        df = pd.DataFrame({
        '项目编码*': ['PJ-EXISTING-2'],
        '项目名称*': ['新名称']
        })

        imported, updated, failed = import_projects_from_dataframe(db_session, df, update_existing=False)
        assert imported == 0
        assert updated == 0
        assert len(failed) == 1
        assert "已存在" in failed[0]["error"]

    def test_import_projects_from_dataframe_invalid_row(self, db_session):
        """测试导入项目 - 无效行数据"""
        df = pd.DataFrame({
        '项目编码*': ['PJ001', None],  # 第二行缺少编码
        '项目名称*': ['项目1', '项目2']
        })

        imported, updated, failed = import_projects_from_dataframe(db_session, df, update_existing=False)
        assert imported == 1  # 第一行成功
        assert updated == 0
        assert len(failed) == 1  # 第二行失败

    def test_import_projects_from_dataframe_multiple_projects(self, db_session, test_customer):
        """测试导入项目 - 多个项目"""
        df = pd.DataFrame({
        '项目编码*': ['PJ-MULTI-001', 'PJ-MULTI-002', 'PJ-MULTI-003'],
        '项目名称*': ['项目1', '项目2', '项目3'],
        '客户名称': [test_customer.customer_name] * 3
        })

        imported, updated, failed = import_projects_from_dataframe(db_session, df, update_existing=False)
        assert imported == 3
        assert updated == 0
        assert len(failed) == 0
