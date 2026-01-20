# -*- coding: utf-8 -*-
"""
Tests for timesheet_report_service
Covers: app/services/timesheet_report_service.py
Coverage Target: 0% -> 60%+
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestTimesheetReportService:
    """工时报表服务测试"""

    @pytest.fixture
    def service(self, db_session: Session):
        """创建服务实例"""
        from app.services.timesheet_report_service import TimesheetReportService
        return TimesheetReportService(db_session)

    @pytest.fixture
    def mock_hr_data(self):
        """模拟HR报表数据"""
        return [
            {
                "employee_name": "张三",
                "department": "研发部",
                "normal_hours": Decimal("160.00"),
                "weekday_overtime": Decimal("20.00"),
                "weekend_overtime": Decimal("10.00"),
                "holiday_overtime": Decimal("5.00"),
                "weekday_overtime_pay": Decimal("1000.00"),
                "weekend_overtime_pay": Decimal("600.00"),
                "holiday_overtime_pay": Decimal("375.00"),
                "total_overtime_pay": Decimal("1975.00"),
            }
        ]

    def test_init_success(self, db_session: Session):
        """测试服务初始化成功"""
        from app.services.timesheet_report_service import TimesheetReportService
        service = TimesheetReportService(db_session)
        assert service.db == db_session
        assert service.aggregation_service is not None
        assert service.overtime_service is not None

    def test_generate_hr_report_excel_structure(
        self, service, db_session: Session, mock_hr_data
    ):
        """测试HR报表Excel结构"""
        with patch.object(
            service.aggregation_service, 'generate_hr_report', return_value=mock_hr_data
        ):
            result = service.generate_hr_report_excel(2025, 1)
            assert result is not None
            assert isinstance(result.read(), bytes)

    def test_generate_hr_report_with_department(
        self, service, db_session: Session, mock_hr_data
    ):
        """测试带部门参数的HR报表生成"""
        with patch.object(
            service.aggregation_service, 'generate_hr_report', return_value=mock_hr_data
        ):
            result = service.generate_hr_report_excel(2025, 1, department_id=1)
            assert result is not None

    def test_generate_finance_report_excel(self, service, db_session: Session):
        """测试财务报表Excel生成"""
        mock_finance_data = [
            {
                "project_code": "PJ001",
                "project_name": "测试项目",
                "department": "研发部",
                "total_hours": Decimal("200.00"),
                "total_cost": Decimal("20000.00"),
            }
        ]

        with patch.object(
            service.aggregation_service, 'generate_finance_report', return_value=mock_finance_data
        ):
            result = service.generate_finance_report_excel(2025, 1)
            assert result is not None

    def test_generate_project_report_excel(self, service, db_session: Session):
        """测试项目工时报表Excel生成"""
        mock_project_data = [
            {
                "project_code": "PJ001",
                "project_name": "测试项目",
                "member_name": "张三",
                "total_hours": Decimal("160.00"),
                "overtime_hours": Decimal("20.00"),
                "billable_hours": Decimal("150.00"),
            }
        ]

        with patch.object(
            service.aggregation_service, 'generate_project_report', return_value=mock_project_data
        ):
            result = service.generate_project_report_excel(1)
            assert result is not None

    def test_generate_attendance_report_excel(self, service, db_session: Session):
        """测试考勤报表Excel生成"""
        mock_attendance_data = [
            {
                "employee_name": "张三",
                "employee_code": "EMP001",
                "department": "研发部",
                "work_days": Decimal("22.00"),
                "leave_days": Decimal("2.00"),
                "absence_days": Decimal("0.00"),
                "overtime_hours": Decimal("35.00"),
            }
        ]

        with patch.object(
            service.aggregation_service, 'generate_attendance_report', return_value=mock_attendance_data
        ):
            result = service.generate_attendance_report_excel(2025, 1)
            assert result is not None

    def test_generate_department_summary_excel(self, service, db_session: Session):
        """测试部门汇总报表Excel生成"""
        mock_dept_data = [
            {
                "department": "研发部",
                "member_count": 10,
                "total_hours": Decimal("1600.00"),
                "overtime_hours": Decimal("200.00"),
                "avg_hours_per_person": Decimal("160.00"),
            }
        ]

        with patch.object(
            service.aggregation_service, 'generate_department_summary', return_value=mock_dept_data
        ):
            result = service.generate_department_summary_excel(2025, 1)
            assert result is not None

    def test_get_report_summary(self, service, db_session: Session):
        """测试报表汇总信息获取"""
        mock_summary = {
            "year": 2025,
            "month": 1,
            "total_employees": 50,
            "total_hours": Decimal("8000.00"),
            "total_overtime": Decimal("1000.00"),
            "total_cost": Decimal("800000.00"),
        }

        with patch.object(
            service.aggregation_service, 'get_report_summary', return_value=mock_summary
        ):
            result = service.get_report_summary(2025, 1)
            assert result == mock_summary

    def test_get_report_summary_with_department(self, service, db_session: Session):
        """测试带部门的报表汇总"""
        mock_summary = {
            "year": 2025,
            "month": 1,
            "department_id": 1,
            "total_employees": 10,
            "total_hours": Decimal("1600.00"),
            "total_overtime": Decimal("200.00"),
            "total_cost": Decimal("160000.00"),
        }

        with patch.object(
            service.aggregation_service, 'get_report_summary', return_value=mock_summary
        ):
            result = service.get_report_summary(2025, 1, department_id=1)
            assert result == mock_summary


class TestTimesheetReportServiceEdgeCases:
    """工时报表服务边界测试"""

    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.timesheet_report_service import TimesheetReportService
        return TimesheetReportService(db_session)

    def test_generate_report_empty_data(self, service, db_session: Session):
        """测试空数据报表生成"""
        with patch.object(
            service.aggregation_service, 'generate_hr_report', return_value=[]
        ):
            result = service.generate_hr_report_excel(2025, 1)
            assert result is not None

    def test_generate_report_none_data(self, service, db_session: Session):
        """测试None数据报表生成"""
        with patch.object(
            service.aggregation_service, 'generate_hr_report', return_value=None
        ):
            result = service.generate_hr_report_excel(2025, 1)
            assert result is not None
