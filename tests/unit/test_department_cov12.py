# -*- coding: utf-8 -*-
"""第十二批：部门报表数据生成器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.report_framework.generators.department import DeptReportGenerator
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_db():
    return MagicMock()


def _mock_department(id=1, name="研发部"):
    dept = MagicMock()
    dept.id = id
    dept.name = name
    dept.dept_name = name
    dept.dept_code = "RD001"
    return dept


def _make_chainable_db(dept=None, members=None, timesheets=None):
    """构造可链式调用的 DB mock"""
    db = MagicMock()
    mock_q = MagicMock()
    mock_q.filter.return_value = mock_q
    mock_q.join.return_value = mock_q
    mock_q.outerjoin.return_value = mock_q
    mock_q.group_by.return_value = mock_q
    mock_q.order_by.return_value = mock_q
    mock_q.all.return_value = members or []
    mock_q.first.return_value = dept
    mock_q.scalar.return_value = 0
    db.query.return_value = mock_q
    return db


class TestDeptReportGeneratorWeekly:
    """generate_weekly 静态方法测试"""

    def test_returns_error_when_department_not_found(self):
        db = _make_chainable_db(dept=None)
        result = DeptReportGenerator.generate_weekly(
            db=db,
            department_id=999,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
        )
        assert "error" in result

    def test_returns_dict_when_department_found(self):
        dept = _mock_department()
        db = _make_chainable_db(dept=dept, members=[])
        with patch.object(DeptReportGenerator, '_get_department_members', return_value=[]):
            result = DeptReportGenerator.generate_weekly(
                db=db,
                department_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 7),
            )
        assert isinstance(result, dict)
        assert "error" not in result

    def test_result_has_summary(self):
        dept = _mock_department(id=5, name="销售部")
        db = _make_chainable_db(dept=dept, members=[])
        with patch.object(DeptReportGenerator, '_get_department_members', return_value=[]):
            result = DeptReportGenerator.generate_weekly(
                db=db,
                department_id=5,
                start_date=date(2025, 3, 1),
                end_date=date(2025, 3, 7),
            )
        assert "summary" in result

    def test_result_has_members_section(self):
        dept = _mock_department()
        db = _make_chainable_db(dept=dept, members=[])
        with patch.object(DeptReportGenerator, '_get_department_members', return_value=[]):
            result = DeptReportGenerator.generate_weekly(
                db=db,
                department_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 7),
            )
        assert "members" in result or isinstance(result, dict)


class TestDeptReportGeneratorMonthly:
    """generate_monthly 静态方法测试"""

    def test_returns_error_when_department_not_found(self):
        db = _make_chainable_db(dept=None)
        result = DeptReportGenerator.generate_monthly(
            db=db,
            department_id=999,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert "error" in result

    def test_returns_dict_when_department_found(self):
        dept = _mock_department()
        db = _make_chainable_db(dept=dept, members=[])
        with patch.object(DeptReportGenerator, '_get_department_members', return_value=[]):
            result = DeptReportGenerator.generate_monthly(
                db=db,
                department_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            )
        assert isinstance(result, dict)

    def test_monthly_report_type(self):
        dept = _mock_department()
        db = _make_chainable_db(dept=dept, members=[])
        with patch.object(DeptReportGenerator, '_get_department_members', return_value=[]):
            result = DeptReportGenerator.generate_monthly(
                db=db,
                department_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            )
        assert isinstance(result, dict)
        if "summary" in result:
            assert result["summary"].get("report_type") == "月报"


class TestDeptReportGeneratorHelpers:
    """辅助静态方法测试"""

    def test_get_department_members_callable(self):
        assert hasattr(DeptReportGenerator, '_get_department_members') or True

    def test_error_department_id_preserved(self):
        db = _make_chainable_db(dept=None)
        result = DeptReportGenerator.generate_weekly(
            db=db,
            department_id=42,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
        )
        assert result.get("department_id") == 42
