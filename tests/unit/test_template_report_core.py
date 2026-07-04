"""
Unit tests for template report core service
Tests coverage for:
- app.services.template_report.core.TemplateReportCore
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.report_center import ReportTemplate
from app.services.template_report.core import TemplateReportCore


class TestGenerateFromTemplate:
    """Test main generate_from_template method"""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create TemplateReportCore instance"""
        return TemplateReportCore(db_session)

    @pytest.fixture
    def template(self):
        """Create a mock report template"""
        template = MagicMock(spec=ReportTemplate)
        template.id = 1
        template.template_code = "T001"
        template.template_name = "Test Template"
        template.report_type = "PROJECT_WEEKLY"
        template.sections = {}
        template.metrics_config = {}
        return template

    def test_generate_with_project_weekly_template(self, service: TemplateReportCore, template):
        """Test generation with PROJECT_WEEKLY type"""
        with patch("app.services.template_report.core.ProjectReportMixin") as mock_mixin:
            mock_mixin._generate_project_weekly.return_value = {"test": "data"}

            result = service.generate_from_template(
                db=service.db,
                template=template,
                project_id=10,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 7),
            )

            assert result is not None
            assert result["template_id"] == 1
            assert result["report_type"] == "PROJECT_WEEKLY"
            mock_mixin._generate_project_weekly.assert_called_once_with(
                service.db,
                10,
                date(2026, 1, 1),
                date(2026, 1, 7),
                {},
                {},
            )

    def test_generate_with_project_monthly_template(self, service: TemplateReportCore, template):
        """Test generation with PROJECT_MONTHLY type"""
        template.report_type = "PROJECT_MONTHLY"
        with patch("app.services.template_report.core.ProjectReportMixin") as mock_mixin:
            mock_mixin._generate_project_monthly.return_value = {"test": "data"}

            result = service.generate_from_template(
                db=service.db,
                template=template,
                project_id=10,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            )

            assert result is not None
            assert result["report_type"] == "PROJECT_MONTHLY"
            mock_mixin._generate_project_monthly.assert_called_once_with(
                service.db,
                10,
                date(2026, 1, 1),
                date(2026, 1, 31),
                {},
                {},
            )

    def test_generate_with_default_dates(self, service: TemplateReportCore, template):
        """Test generation uses default date range (last 30 days)"""
        with patch("app.services.template_report.core.ProjectReportMixin") as mock_mixin:
            mock_mixin._generate_project_weekly.return_value = {"test": "data"}

            today = date.today()
            expected_start = today - timedelta(days=30)

            result = service.generate_from_template(db=service.db, template=template, project_id=10)

            assert result is not None
            assert result["period"]["start_date"] == expected_start.isoformat()
            assert result["period"]["end_date"] == today.isoformat()

    def test_generate_with_filters(self, service: TemplateReportCore, template):
        """Test filters are accepted and generic reports receive the report type."""
        template.report_type = "CUSTOM_REPORT"
        with patch("app.services.template_report.core.GenericReportMixin") as mock_mixin:
            mock_mixin._generate_generic_report.return_value = {"test": "data"}

            filters = {"custom_field": "test_value"}

            result = service.generate_from_template(
                db=service.db, template=template, project_id=10, filters=filters
            )

            assert result is not None
            mock_mixin._generate_generic_report.assert_called_once_with(
                service.db,
                "CUSTOM_REPORT",
                10,
                None,
                result["period"]["start_date"] and date.fromisoformat(result["period"]["start_date"]),
                result["period"]["end_date"] and date.fromisoformat(result["period"]["end_date"]),
            )
