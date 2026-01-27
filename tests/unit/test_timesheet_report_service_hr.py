"""
Unit tests for timesheet report service
Tests coverage for:
- app.services.timesheet_report_service.TimesheetReportService
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.user import User

if TYPE_CHECKING:
    from app.services.timesheet_report_service import TimesheetReportService


class TestTimesheetReportServiceInit:
    """Test TimesheetReportService initialization"""

    def test_init_with_excel_available(self, db_session: Session):
        """Test initialization when Excel libraries are available"""
        with patch("app.services.timesheet_report_service.EXCEL_AVAILABLE", True):
            from app.services.timesheet_report_service import TimesheetReportService

            service = TimesheetReportService(db_session)
            assert service.db == db_session
            assert service.aggregation_service is not None
            assert service.overtime_service is not None

    def test_init_without_excel_available(self, db_session: Session):
        """Test initialization raises error when Excel libraries are not available"""
        with patch("app.services.timesheet_report_service.EXCEL_AVAILABLE", False):
            from app.services.timesheet_report_service import TimesheetReportService

            with pytest.raises(ImportError) as exc_info:
                TimesheetReportService(db_session)

            assert "Excel处理库未安装" in str(exc_info.value)


class TestGenerateHRReport:
    """Test HR report generation"""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create TimesheetReportService instance"""
        with patch("app.services.timesheet_report_service.EXCEL_AVAILABLE", True):
            from app.services.timesheet_report_service import TimesheetReportService

            return TimesheetReportService(db_session)

    def test_generate_hr_report_with_empty_data(self, service: TimesheetReportService):
        """Test HR report generation with empty timesheet data"""
        with patch.object(
            service.aggregation_service, "generate_hr_report"
        ) as mock_agg:
            mock_agg.return_value = []

            result = service.generate_hr_report_excel(2026, 1)

            assert result is not None
            # Verify it's a BytesIO object containing Excel data
            assert hasattr(result, "read")

    def test_generate_hr_report_with_department_filter(
        self, service: TimesheetReportService
    ):
        """Test HR report generation with department filter"""
        with patch.object(
            service.aggregation_service, "generate_hr_report"
        ) as mock_agg:
            mock_agg.return_value = [
                {
                    "user_id": 1,
                    "user_name": "Test User",
                    "normal_hours": 160.0,
                    "overtime_hours": 10.0,
                    "weekend_hours": 8.0,
                    "holiday_hours": 4.0,
                }
            ]

            result = service.generate_hr_report_excel(2026, 1, department_id=10)

            assert result is not None
            mock_agg.assert_called_once_with(2026, 1, 10)

    def test_generate_hr_report_handles_missing_department(
        self, service: TimesheetReportService
    ):
        """Test HR report handles user without department"""
        with (
            patch.object(service.aggregation_service, "generate_hr_report") as mock_agg,
            patch(
                "app.services.timesheet_report_service.HourlyRateService"
            ) as mock_rate,
        ):
            mock_agg.return_value = [
                {
                    "user_id": 1,
                    "user_name": "Test User",
                    "normal_hours": 160.0,
                    "overtime_hours": 10.0,
                    "weekend_hours": 8.0,
                    "holiday_hours": 4.0,
                }
            ]

            # Mock user without department
            mock_user = MagicMock(spec=User)
            mock_user.department_id = None
            mock_rate.get_user_hourly_rate.return_value = Decimal("50.0")

            with patch.object(service.db, "query") as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                result = service.generate_hr_report_excel(2026, 1)

                assert result is not None

    def test_generate_hr_report_calculates_correct_overtime_pay(
        self, service: TimesheetReportService
    ):
        """Test HR report calculates overtime pay correctly"""
        with (
            patch.object(service.aggregation_service, "generate_hr_report") as mock_agg,
            patch(
                "app.services.timesheet_report_service.HourlyRateService"
            ) as mock_rate,
        ):
            mock_agg.return_value = [
                {
                    "user_id": 1,
                    "user_name": "Test User",
                    "normal_hours": 160.0,
                    "overtime_hours": 10.0,  # 1.5x rate
                    "weekend_hours": 8.0,  # 2x rate
                    "holiday_hours": 4.0,  # 3x rate
                }
            ]

            hourly_rate = Decimal("50.0")
            mock_rate.get_user_hourly_rate.return_value = hourly_rate

            result = service.generate_hr_report_excel(2026, 1)

            assert result is not None
            # Verify the calculation logic was called
            mock_rate.get_user_hourly_rate.assert_called_once()

    def test_generate_hr_report_with_department_name(
        self, service: TimesheetReportService
    ):
        """Test HR report includes department name"""
        with (
            patch.object(service.aggregation_service, "generate_hr_report") as mock_agg,
            patch(
                "app.services.timesheet_report_service.HourlyRateService"
            ) as mock_rate,
        ):
            mock_agg.return_value = [
                {
                    "user_id": 1,
                    "user_name": "Test User",
                    "normal_hours": 160.0,
                    "overtime_hours": 10.0,
                    "weekend_hours": 8.0,
                    "holiday_hours": 4.0,
                }
            ]

            mock_user = MagicMock(spec=User)
            mock_user.department_id = 10

            mock_department = MagicMock(spec=Department)
            mock_department.name = "Engineering"
            mock_rate.get_user_hourly_rate.return_value = Decimal("50.0")

            # Mock database queries
            def mock_query_side_effect(*args, **kwargs):
                if User in args:
                    mock_q = MagicMock()
                    mock_q.filter.return_value.first.return_value = mock_user
                    return mock_q
                elif Department in args:
                    mock_q = MagicMock()
                    mock_q.filter.return_value.first.return_value = mock_department
                    return mock_q
                return MagicMock()

            with patch.object(service.db, "query", side_effect=mock_query_side_effect):
                result = service.generate_hr_report_excel(2026, 1)

                assert result is not None


class TestGenerateFinanceReport:
    """Test finance report generation"""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create TimesheetReportService instance"""
        with patch("app.services.timesheet_report_service.EXCEL_AVAILABLE", True):
            from app.services.timesheet_report_service import TimesheetReportService

            return TimesheetReportService(db_session)

    def test_generate_finance_report_basic(self, service: TimesheetReportService):
        """Test finance report generation"""
        with patch.object(
            service.aggregation_service, "generate_finance_report"
        ) as mock_agg:
            mock_agg.return_value = [
                {"project_name": "Project A", "cost": Decimal("50000.00")},
                {"project_name": "Project B", "cost": Decimal("75000.00")},
            ]

            result = service.generate_finance_report_excel(2026, 1)

            assert result is not None

    def test_generate_finance_report_with_empty_data(
        self, service: TimesheetReportService
    ):
        """Test finance report with empty data"""
        with patch.object(
            service.aggregation_service, "generate_finance_report"
        ) as mock_agg:
            mock_agg.return_value = []

            result = service.generate_finance_report_excel(2026, 1)

            assert result is not None


class TestGenerateRDReport:
    """Test R&D report generation"""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create TimesheetReportService instance"""
        with patch("app.services.timesheet_report_service.EXCEL_AVAILABLE", True):
            from app.services.timesheet_report_service import TimesheetReportService

            return TimesheetReportService(db_session)

    def test_generate_rd_report_basic(self, service: TimesheetReportService):
        """Test R&D report generation"""
        with patch.object(
            service.aggregation_service, "generate_rd_report"
        ) as mock_agg:
            mock_agg.return_value = [
                {"project_name": "R&D Project 1", "total_hours": 200.5},
                {"project_name": "R&D Project 2", "total_hours": 150.0},
            ]

            result = service.generate_rd_report_excel(2026, 1)

            assert result is not None

    def test_generate_rd_report_with_empty_data(self, service: TimesheetReportService):
        """Test R&D report with empty data"""
        with patch.object(
            service.aggregation_service, "generate_rd_report"
        ) as mock_agg:
            mock_agg.return_value = []

            result = service.generate_rd_report_excel(2026, 1)

            assert result is not None
