# -*- coding: utf-8 -*-
"""Tests for app/schemas/organization.py"""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeHrProfileCreate,
    EmployeeHrProfileUpdate,
    EmployeeHrProfileResponse,
    HrTransactionCreate,
    EmployeeContractCreate,
    EmployeeContractUpdate,
    OrganizationUnitCreate,
    OrganizationUnitUpdate,
    PositionCreate,
    PositionUpdate,
    JobLevelCreate,
    JobLevelUpdate,
    EmployeeOrgAssignmentCreate,
)


class TestDepartmentCreate:
    def test_valid(self):
        d = DepartmentCreate(dept_code="D001", dept_name="技术部")
        assert d.level == 1
        assert d.sort_order == 0

    def test_missing_code(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(dept_name="技术部")

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(dept_code="D001")

    def test_long_code(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(dept_code="x" * 21, dept_name="T")

    def test_with_parent(self):
        d = DepartmentCreate(dept_code="D002", dept_name="子部门", parent_id=1, manager_id=10)
        assert d.parent_id == 1


class TestDepartmentUpdate:
    def test_all_none(self):
        d = DepartmentUpdate()
        assert d.dept_name is None

    def test_partial(self):
        d = DepartmentUpdate(dept_name="新名称", is_active=False)
        assert d.is_active is False


class TestDepartmentResponse:
    def test_valid(self):
        d = DepartmentResponse(id=1, dept_code="D001", dept_name="T", level=1, sort_order=0, is_active=True)
        assert d.parent_id is None


class TestEmployeeCreate:
    def test_valid(self):
        e = EmployeeCreate(employee_code="E001", name="张三")
        assert e.department is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            EmployeeCreate()

    def test_long_code(self):
        with pytest.raises(ValidationError):
            EmployeeCreate(employee_code="x" * 11, name="T")

    def test_full(self):
        e = EmployeeCreate(
            employee_code="E001", name="张三",
            department="IT", role="Dev", phone="123", wechat_userid="wx001"
        )
        assert e.wechat_userid == "wx001"


class TestEmployeeUpdate:
    def test_all_none(self):
        e = EmployeeUpdate()
        assert e.name is None

    def test_partial(self):
        e = EmployeeUpdate(name="李四", is_active=False)
        assert e.is_active is False


class TestEmployeeResponse:
    def test_valid(self):
        e = EmployeeResponse(id=1, employee_code="E001", name="张三", is_active=True)
        assert e.employment_status is None


class TestEmployeeHrProfileCreate:
    def test_valid(self):
        p = EmployeeHrProfileCreate(employee_id=1)
        assert p.dept_level1 is None
        assert p.is_confirmed is False

    def test_with_details(self):
        p = EmployeeHrProfileCreate(
            employee_id=1,
            dept_level1="技术中心",
            hire_date=date(2024, 1, 1),
            gender="男",
            height_cm=Decimal("175.5"),
            weight_kg=Decimal("70.0"),
        )
        assert p.height_cm == Decimal("175.5")

    def test_missing_employee_id(self):
        with pytest.raises(ValidationError):
            EmployeeHrProfileCreate()


class TestHrTransactionCreate:
    def test_valid(self):
        t = HrTransactionCreate(
            employee_id=1,
            transaction_type="onboarding",
            transaction_date=date(2024, 6, 1),
        )
        assert t.resignation_date is None

    def test_resignation(self):
        t = HrTransactionCreate(
            employee_id=1, transaction_type="resignation",
            transaction_date=date(2024, 6, 1),
            resignation_date=date(2024, 6, 30),
            resignation_reason="个人原因",
        )
        assert t.resignation_reason == "个人原因"

    def test_missing(self):
        with pytest.raises(ValidationError):
            HrTransactionCreate()


class TestEmployeeContractCreate:
    def test_valid(self):
        c = EmployeeContractCreate(
            employee_id=1, contract_type="fixed_term",
            start_date=date(2024, 1, 1),
        )
        assert c.end_date is None

    def test_with_salary(self):
        c = EmployeeContractCreate(
            employee_id=1, contract_type="fixed_term",
            start_date=date(2024, 1, 1),
            base_salary=Decimal("10000"),
            probation_salary=Decimal("8000"),
        )
        assert c.base_salary == Decimal("10000")

    def test_missing(self):
        with pytest.raises(ValidationError):
            EmployeeContractCreate()


class TestOrganizationUnitCreate:
    def test_valid(self):
        o = OrganizationUnitCreate(
            unit_code="ORG001", unit_name="总部", unit_type="COMPANY"
        )
        assert o.sort_order == 0

    def test_missing(self):
        with pytest.raises(ValidationError):
            OrganizationUnitCreate()


class TestPositionCreate:
    def test_valid(self):
        p = PositionCreate(
            position_code="P001", position_name="工程师",
            position_category="TECHNICAL",
        )
        assert p.sort_order == 0

    def test_missing(self):
        with pytest.raises(ValidationError):
            PositionCreate()


class TestJobLevelCreate:
    def test_valid(self):
        j = JobLevelCreate(
            level_code="P5", level_name="高级工程师",
            level_category="P", level_rank=5,
        )
        assert j.sort_order == 0

    def test_missing(self):
        with pytest.raises(ValidationError):
            JobLevelCreate()


class TestEmployeeOrgAssignmentCreate:
    def test_valid(self):
        a = EmployeeOrgAssignmentCreate(employee_id=1, org_unit_id=1)
        assert a.is_primary is True
        assert a.assignment_type == "PERMANENT"

    def test_with_dates(self):
        a = EmployeeOrgAssignmentCreate(
            employee_id=1, org_unit_id=2,
            position_id=3, job_level_id=4,
            start_date=date(2024, 1, 1),
        )
        assert a.position_id == 3
